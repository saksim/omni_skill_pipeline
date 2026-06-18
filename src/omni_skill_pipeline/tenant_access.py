from __future__ import annotations

import hmac
import json
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omni_skill_pipeline.models import (
    Membership,
    MembershipRole,
    Organization,
    Project,
    TenantAPIKey,
    TenantQuotaPolicy,
    TenantUser,
)

_DISTILL_ACTION = "distill.execute"
_REVIEW_READ_ACTION = "review.read"
_REVIEW_WRITE_ACTION = "review.write"


_ROLE_ACTIONS: dict[str, set[str]] = {
    MembershipRole.OWNER.value: {_DISTILL_ACTION, _REVIEW_READ_ACTION, _REVIEW_WRITE_ACTION},
    MembershipRole.OPERATOR.value: {_DISTILL_ACTION, _REVIEW_READ_ACTION, _REVIEW_WRITE_ACTION},
    MembershipRole.REVIEWER.value: {_REVIEW_READ_ACTION, _REVIEW_WRITE_ACTION},
    MembershipRole.CONTRIBUTOR.value: {_DISTILL_ACTION, _REVIEW_READ_ACTION},
    MembershipRole.VIEWER.value: {_REVIEW_READ_ACTION},
}


@dataclass(frozen=True, slots=True)
class TenantIdentity:
    organization_id: str
    project_id: str
    user_id: str
    role: str
    api_key_id: str

    def to_scope_dict(self) -> dict[str, str]:
        return {
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "role": self.role,
            "api_key_id": self.api_key_id,
        }


@dataclass(frozen=True, slots=True)
class TenantAuthResult:
    identity: TenantIdentity | None
    failure_code: str = ""
    message: str = ""


class TenantQuotaLimiter(object):
    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = {}
        self._lock = threading.Lock()

    def allow(
        self,
        *,
        quota_key: tuple[str, str],
        max_requests: int,
        window_seconds: int,
        now: float | None = None,
    ) -> tuple[bool, int]:
        if max_requests <= 0 or window_seconds <= 0:
            return True, 0
        now_ts = time.monotonic() if now is None else now
        cutoff = now_ts - float(window_seconds)

        with self._lock:
            events = self._events.get(quota_key)
            if events is None:
                events = deque()
                self._events[quota_key] = events

            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= max_requests:
                retry_after = max(1, int(events[0] + window_seconds - now_ts))
                return False, retry_after
            events.append(now_ts)
            return True, 0


class TenantAccessRegistry(object):
    def __init__(
        self,
        *,
        organizations: list[Organization],
        projects: list[Project],
        users: list[TenantUser],
        memberships: list[Membership],
        api_keys: list[TenantAPIKey],
        quota_policies: list[TenantQuotaPolicy],
    ) -> None:
        self.organizations = organizations
        self.projects = projects
        self.users = users
        self.memberships = memberships
        self.api_keys = api_keys
        self.quota_policies = quota_policies
        self._quota_limiter = TenantQuotaLimiter()

    @classmethod
    def from_settings(cls, settings: Any) -> TenantAccessRegistry | None:
        payload_text = str(getattr(settings, "tenant_access_json", "") or "").strip()
        access_file = str(getattr(settings, "tenant_access_file", "") or "").strip()
        if not payload_text and not access_file:
            return None
        if not payload_text and access_file:
            path = Path(access_file)
            if not path.is_absolute():
                repo_root = getattr(settings, "repo_root", None)
                if repo_root is not None:
                    path = Path(repo_root) / path
            payload_text = path.read_text(encoding="utf-8")

        payload = json.loads(payload_text)
        if not isinstance(payload, dict):
            raise ValueError("Tenant access payload must be a JSON object.")
        return cls.from_dict(payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TenantAccessRegistry:
        organizations = cls._parse_organizations(payload.get("organizations"))
        projects = cls._parse_projects(payload.get("projects"))
        users = cls._parse_users(payload.get("users"))
        memberships = cls._parse_memberships(payload.get("memberships"))
        api_keys = cls._parse_api_keys(payload.get("api_keys"))
        quota_policies = cls._parse_quota_policies(payload.get("quota_policies"))

        organization_ids = {item.organization_id for item in organizations}
        project_keys = {(item.organization_id, item.project_id) for item in projects}
        user_keys = {(item.organization_id, item.user_id) for item in users}

        for item in projects:
            if organization_ids and item.organization_id not in organization_ids:
                raise ValueError("Project references unknown organization_id: %s" % item.organization_id)
        for item in users:
            if organization_ids and item.organization_id not in organization_ids:
                raise ValueError("User references unknown organization_id: %s" % item.organization_id)
        for item in memberships:
            if organization_ids and item.organization_id not in organization_ids:
                raise ValueError("Membership references unknown organization_id: %s" % item.organization_id)
            if project_keys and (item.organization_id, item.project_id) not in project_keys:
                raise ValueError(
                    "Membership references unknown project_id %s for organization_id %s."
                    % (item.project_id, item.organization_id)
                )
            if user_keys and (item.organization_id, item.user_id) not in user_keys:
                raise ValueError(
                    "Membership references unknown user_id %s for organization_id %s."
                    % (item.user_id, item.organization_id)
                )
        for item in api_keys:
            if organization_ids and item.organization_id not in organization_ids:
                raise ValueError("API key references unknown organization_id: %s" % item.organization_id)
            if project_keys and (item.organization_id, item.project_id) not in project_keys:
                raise ValueError(
                    "API key references unknown project_id %s for organization_id %s."
                    % (item.project_id, item.organization_id)
                )
            if user_keys and (item.organization_id, item.user_id) not in user_keys:
                raise ValueError(
                    "API key references unknown user_id %s for organization_id %s."
                    % (item.user_id, item.organization_id)
                )
        for item in quota_policies:
            if organization_ids and item.organization_id not in organization_ids:
                raise ValueError("Quota policy references unknown organization_id: %s" % item.organization_id)
            if project_keys and (item.organization_id, item.project_id) not in project_keys:
                raise ValueError(
                    "Quota policy references unknown project_id %s for organization_id %s."
                    % (item.project_id, item.organization_id)
                )

        return cls(
            organizations=organizations,
            projects=projects,
            users=users,
            memberships=memberships,
            api_keys=api_keys,
            quota_policies=quota_policies,
        )

    def authenticate(self, provided_api_key: str) -> TenantAuthResult:
        provided = str(provided_api_key or "").strip()
        if not provided:
            return TenantAuthResult(identity=None, failure_code="missing_api_key", message="Missing API key.")

        for item in self.api_keys:
            if not hmac.compare_digest(provided, item.api_key):
                continue
            if item.revoked:
                return TenantAuthResult(identity=None, failure_code="revoked_api_key", message="API key revoked.")
            identity = TenantIdentity(
                organization_id=item.organization_id,
                project_id=item.project_id,
                user_id=item.user_id,
                role=item.role,
                api_key_id=item.api_key_id,
            )
            return TenantAuthResult(identity=identity)
        return TenantAuthResult(identity=None, failure_code="invalid_api_key", message="Invalid API key.")

    def authorize(self, *, identity: TenantIdentity, action: str) -> bool:
        allowed_actions = _ROLE_ACTIONS.get(identity.role, set())
        if action not in allowed_actions:
            return False
        key_payload = self._find_api_key(identity.api_key_id)
        if key_payload is None:
            return False
        scopes = [str(item).strip() for item in key_payload.scopes if str(item).strip()]
        if scopes and action not in scopes:
            return False
        return True

    def validate_requested_scope(
        self,
        *,
        identity: TenantIdentity,
        requested_scope: dict[str, Any] | None,
    ) -> bool:
        if not isinstance(requested_scope, dict) or not requested_scope:
            return True
        organization_id = str(requested_scope.get("organization_id", "")).strip()
        project_id = str(requested_scope.get("project_id", "")).strip()
        if organization_id and organization_id != identity.organization_id:
            return False
        if project_id and project_id != identity.project_id:
            return False
        return True

    def enforce_quota(self, *, identity: TenantIdentity, action: str) -> tuple[bool, int]:
        api_key = self._find_api_key(identity.api_key_id)
        if api_key is None:
            return False, 0
        quota = api_key.quota_policy
        if action == _DISTILL_ACTION:
            return self._quota_limiter.allow(
                quota_key=(identity.api_key_id, action),
                max_requests=int(quota.distill_requests_per_window),
                window_seconds=int(quota.window_seconds),
            )
        if action == _REVIEW_WRITE_ACTION:
            return self._quota_limiter.allow(
                quota_key=(identity.api_key_id, action),
                max_requests=int(quota.review_actions_per_window),
                window_seconds=int(quota.window_seconds),
            )
        return True, 0

    def _find_api_key(self, api_key_id: str) -> TenantAPIKey | None:
        key_id = str(api_key_id).strip()
        for item in self.api_keys:
            if item.api_key_id == key_id:
                return item
        return None

    @staticmethod
    def _parse_organizations(payload: Any) -> list[Organization]:
        if payload is None:
            return []
        if not isinstance(payload, list):
            raise ValueError("organizations must be a list.")
        organizations: list[Organization] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("organization item must be an object.")
            organizations.append(
                Organization(
                    organization_id=str(item.get("organization_id", "")).strip(),
                    name=str(item.get("name", "")).strip(),
                    metadata=item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {},
                )
            )
        return organizations

    @staticmethod
    def _parse_projects(payload: Any) -> list[Project]:
        if payload is None:
            return []
        if not isinstance(payload, list):
            raise ValueError("projects must be a list.")
        projects: list[Project] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("project item must be an object.")
            projects.append(
                Project(
                    project_id=str(item.get("project_id", "")).strip(),
                    organization_id=str(item.get("organization_id", "")).strip(),
                    name=str(item.get("name", "")).strip(),
                    metadata=item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {},
                )
            )
        return projects

    @staticmethod
    def _parse_users(payload: Any) -> list[TenantUser]:
        if payload is None:
            return []
        if not isinstance(payload, list):
            raise ValueError("users must be a list.")
        users: list[TenantUser] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("user item must be an object.")
            users.append(
                TenantUser(
                    user_id=str(item.get("user_id", "")).strip(),
                    organization_id=str(item.get("organization_id", "")).strip(),
                    name=str(item.get("name", "")).strip(),
                    email=str(item.get("email", "")).strip(),
                    metadata=item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {},
                )
            )
        return users

    @staticmethod
    def _parse_memberships(payload: Any) -> list[Membership]:
        if payload is None:
            return []
        if not isinstance(payload, list):
            raise ValueError("memberships must be a list.")
        memberships: list[Membership] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("membership item must be an object.")
            memberships.append(
                Membership(
                    membership_id=str(item.get("membership_id", "")).strip(),
                    organization_id=str(item.get("organization_id", "")).strip(),
                    project_id=str(item.get("project_id", "")).strip(),
                    user_id=str(item.get("user_id", "")).strip(),
                    role=MembershipRole(str(item.get("role", MembershipRole.CONTRIBUTOR.value)).strip() or MembershipRole.CONTRIBUTOR.value).value,
                    metadata=item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {},
                )
            )
        return memberships

    @staticmethod
    def _parse_quota_policy(payload: Any) -> TenantQuotaPolicy:
        if not isinstance(payload, dict):
            return TenantQuotaPolicy()
        return TenantQuotaPolicy(
            quota_id=str(payload.get("quota_id", "")).strip(),
            organization_id=str(payload.get("organization_id", "")).strip(),
            project_id=str(payload.get("project_id", "")).strip(),
            distill_requests_per_window=max(0, int(payload.get("distill_requests_per_window", 0) or 0)),
            review_actions_per_window=max(0, int(payload.get("review_actions_per_window", 0) or 0)),
            window_seconds=max(1, int(payload.get("window_seconds", 60) or 60)),
            metadata=payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {},
        )

    @classmethod
    def _parse_api_keys(cls, payload: Any) -> list[TenantAPIKey]:
        if payload is None:
            return []
        if not isinstance(payload, list):
            raise ValueError("api_keys must be a list.")
        keys: list[TenantAPIKey] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("api_key item must be an object.")
            scopes_payload = item.get("scopes", [])
            if not isinstance(scopes_payload, list):
                raise ValueError("api_key.scopes must be a list when provided.")
            scopes = [str(scope).strip() for scope in scopes_payload if str(scope).strip()]
            role_text = str(item.get("role", MembershipRole.CONTRIBUTOR.value)).strip() or MembershipRole.CONTRIBUTOR.value
            role = MembershipRole(role_text).value
            keys.append(
                TenantAPIKey(
                    api_key_id=str(item.get("api_key_id", "")).strip(),
                    api_key=str(item.get("api_key", "")).strip(),
                    organization_id=str(item.get("organization_id", "")).strip(),
                    project_id=str(item.get("project_id", "")).strip(),
                    user_id=str(item.get("user_id", "")).strip(),
                    role=role,
                    scopes=scopes,
                    revoked=bool(item.get("revoked", False)),
                    quota_policy=cls._parse_quota_policy(item.get("quota_policy")),
                    metadata=item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {},
                )
            )
        return keys

    @classmethod
    def _parse_quota_policies(cls, payload: Any) -> list[TenantQuotaPolicy]:
        if payload is None:
            return []
        if not isinstance(payload, list):
            raise ValueError("quota_policies must be a list.")
        policies: list[TenantQuotaPolicy] = []
        for item in payload:
            policies.append(cls._parse_quota_policy(item))
        return policies

