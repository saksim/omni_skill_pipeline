from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_TEXT_TITLE = "Internal dogfood text smoke"
DEFAULT_TEXT_CONTENT = (
    "Incident note: API health was checked, template retrieval worked, "
    "and the reviewer must confirm the generated skill before publication."
)


@dataclass(frozen=True)
class SmokeConfig:
    base_url: str
    api_key: str
    timeout_seconds: float
    title: str
    content: str
    dry_run: bool


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the internal dogfood API happy path: healthz, template, "
            "text distill, and review queue visibility."
        ),
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--title", default=DEFAULT_TEXT_TITLE)
    parser.add_argument("--content", default=DEFAULT_TEXT_CONTENT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default="", help='Optional JSON report output path. Use "-" to print only.')
    parser.add_argument("--summary-output", default="", help='Optional Markdown summary output path.')
    return parser


def _to_config(args: argparse.Namespace) -> SmokeConfig:
    return SmokeConfig(
        base_url=str(args.base_url or "").strip().rstrip("/") or DEFAULT_BASE_URL,
        api_key=str(args.api_key or "").strip(),
        timeout_seconds=max(float(args.timeout_seconds), 1.0),
        title=str(args.title or "").strip() or DEFAULT_TEXT_TITLE,
        content=str(args.content or "").strip() or DEFAULT_TEXT_CONTENT,
        dry_run=bool(args.dry_run),
    )


def _headers(config: SmokeConfig) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if config.api_key:
        headers["X-API-Key"] = config.api_key
    return headers


def _url(config: SmokeConfig, path: str, query: dict[str, Any] | None = None) -> str:
    url = "%s/%s" % (config.base_url, path.lstrip("/"))
    if query:
        return "%s?%s" % (url, urllib.parse.urlencode(query))
    return url


def _request_json(
    config: SmokeConfig,
    *,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    body = None
    headers = _headers(config)
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        _url(config, path, query),
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            return int(getattr(response, "status", 0)), _parse_response_body(response_body)
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        return int(exc.code), _parse_response_body(response_body)


def _parse_response_body(raw: str) -> Any:
    text = str(raw or "")
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _check_http_ok(name: str, status_code: int, payload: Any) -> dict[str, Any]:
    ok = 200 <= int(status_code) < 300
    return {
        "name": name,
        "ok": ok,
        "status_code": int(status_code),
        "detail": "ok" if ok else "unexpected HTTP status",
        "payload": payload,
    }


def _distill_text(config: SmokeConfig) -> tuple[int, Any]:
    return _request_json(
        config,
        method="POST",
        path="/v1/distill/text",
        payload={
            "title": config.title,
            "content": config.content,
            "goal": {
                "goal_type": "build_skill",
                "audience": "self",
                "rigor": "draft",
                "granularity": "task",
                "domain": "internal-dogfood",
            },
            "metadata": {
                "internal_dogfood_only": True,
                "source": "scripts/internal_dogfood_smoke.py",
            },
        },
    )


def _extract_review_task_id(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    review_task = payload.get("review_task")
    if isinstance(review_task, dict):
        return str(review_task.get("review_task_id", "")).strip()
    adapter_metadata = payload.get("adapter_metadata")
    if isinstance(adapter_metadata, dict):
        review_task = adapter_metadata.get("review_task")
        if isinstance(review_task, dict):
            return str(review_task.get("review_task_id", "")).strip()
    return ""


def _extract_review_status(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in ("review_status", "status"):
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    review_task = payload.get("review_task")
    if isinstance(review_task, dict):
        return str(review_task.get("status", "")).strip()
    return ""


def _queue_contains_task(payload: Any, review_task_id: str) -> bool:
    if not review_task_id or not isinstance(payload, dict):
        return False
    items = payload.get("items")
    if not isinstance(items, list):
        return False
    for item in items:
        if isinstance(item, dict) and str(item.get("review_task_id", "")).strip() == review_task_id:
            return True
    return False


def _build_report(config: SmokeConfig) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    health_status, health_payload = _request_json(config, method="GET", path="/healthz")
    checks.append(_check_http_ok("healthz", health_status, health_payload))

    template_status, template_payload = _request_json(config, method="GET", path="/v1/templates/skill")
    template_check = _check_http_ok("template", template_status, template_payload)
    template_check["ok"] = template_check["ok"] and bool(str(template_payload).strip())
    if not template_check["ok"]:
        template_check["detail"] = "template response is empty or unavailable"
    checks.append(template_check)

    distill_status, distill_payload = _distill_text(config)
    distill_check = _check_http_ok("distill_text", distill_status, distill_payload)
    if isinstance(distill_payload, dict):
        has_skill_output = bool(
            str(distill_payload.get("skill_markdown", "")).strip()
            or str(distill_payload.get("ok", "")).strip()
        )
    else:
        has_skill_output = False
    distill_check["ok"] = distill_check["ok"] and has_skill_output
    if not distill_check["ok"]:
        distill_check["detail"] = "distill text did not return a skill payload"
    checks.append(distill_check)

    queue_status, queue_payload = _request_json(
        config,
        method="GET",
        path="/v1/review/queue",
        query={"queue_status": "pending", "limit": 20},
    )
    queue_check = _check_http_ok("review_queue", queue_status, queue_payload)
    queue_items = queue_payload.get("items") if isinstance(queue_payload, dict) else None
    queue_check["ok"] = queue_check["ok"] and isinstance(queue_items, list)
    if not queue_check["ok"]:
        queue_check["detail"] = "review queue did not return an items list"
    checks.append(queue_check)

    review_task_id = _extract_review_task_id(distill_payload)
    review_status = _extract_review_status(distill_payload)
    if review_task_id or review_status == "review_pending":
        queue_trace_check = {
            "name": "review_queue_trace",
            "ok": _queue_contains_task(queue_payload, review_task_id),
            "status_code": queue_status,
            "detail": "distilled review task is visible in pending queue",
            "review_task_id": review_task_id,
            "review_status": review_status,
        }
        if not queue_trace_check["ok"]:
            queue_trace_check["detail"] = "distilled review task was not visible in pending queue"
        checks.append(queue_trace_check)

    ok = all(bool(check.get("ok")) for check in checks)
    return {
        "schema_version": "internal_dogfood_smoke.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "internal_dogfood_only",
        "base_url": config.base_url,
        "decision": "PASS" if ok else "FAIL",
        "check_count": len(checks),
        "pass_count": sum(1 for check in checks if check.get("ok")),
        "fail_count": sum(1 for check in checks if not check.get("ok")),
        "review_task_id": review_task_id,
        "checks": checks,
    }


def _build_unreachable_report(config: SmokeConfig, exc: BaseException) -> dict[str, Any]:
    return {
        "schema_version": "internal_dogfood_smoke.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "internal_dogfood_only",
        "base_url": config.base_url,
        "decision": "FAIL",
        "failure_category": "api_unreachable",
        "failure_message": str(exc),
        "check_count": 1,
        "pass_count": 0,
        "fail_count": 1,
        "review_task_id": "",
        "checks": [
            {
                "name": "api_reachable",
                "ok": False,
                "status_code": 0,
                "detail": "API was not reachable.",
                "error": str(exc),
            }
        ],
    }


def _render_markdown(report: dict[str, Any]) -> str:
    failed_checks = [
        str(check.get("name", "")).strip()
        for check in report.get("checks", [])
        if isinstance(check, dict) and not check.get("ok")
    ]
    failed_text = ", ".join(item for item in failed_checks if item) or "none"
    return "\n".join(
        [
            "# Internal Dogfood API Smoke Summary",
            "",
            "- Decision: `%s`" % report.get("decision", "FAIL"),
            "- Scope: `%s`" % report.get("scope", "internal_dogfood_only"),
            "- Base URL: `%s`" % report.get("base_url", ""),
            "- Checks: `%s` pass / `%s` fail / `%s` total"
            % (report.get("pass_count", 0), report.get("fail_count", 0), report.get("check_count", 0)),
            "- Review task: `%s`" % (report.get("review_task_id") or "none"),
            "- Failed checks: `%s`" % failed_text,
            "",
            "This smoke result is internal-dogfood evidence only; it is not an external Beta, GA, or SaaS launch claim.",
            "",
        ]
    )


def _write_text(path_value: str, content: str) -> None:
    path = Path(path_value).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _print_plan(config: SmokeConfig) -> None:
    print("Plan: GET %s" % _url(config, "/healthz"))
    print("Plan: GET %s" % _url(config, "/v1/templates/skill"))
    print("Plan: POST %s" % _url(config, "/v1/distill/text"))
    print("Plan: GET %s" % _url(config, "/v1/review/queue", {"queue_status": "pending", "limit": 20}))


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = _to_config(args)
    _print_plan(config)
    if config.dry_run:
        return 0
    try:
        report = _build_report(config)
    except urllib.error.URLError as exc:
        print("Internal dogfood smoke failed to reach API: %s" % exc, file=sys.stderr)
        report = _build_unreachable_report(config, exc)
    summary = _render_markdown(report)
    if str(args.output or "").strip() and str(args.output).strip() != "-":
        _write_text(str(args.output).strip(), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Internal dogfood smoke report written: %s" % Path(str(args.output).strip()).resolve())
    if str(args.summary_output or "").strip() and str(args.summary_output).strip() != "-":
        _write_text(str(args.summary_output).strip(), summary)
        print("Internal dogfood smoke summary written: %s" % Path(str(args.summary_output).strip()).resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
