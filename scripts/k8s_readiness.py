from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "k8s_readiness.v1"
CLUSTER_EVIDENCE_SCHEMA_VERSION = "k8s_cluster_evidence.v1"
DEFAULT_MANIFEST_DIR = REPO_ROOT / "k8s"
DEFAULT_PRODUCTION_OPS_RUNBOOK = (
    REPO_ROOT / "docs" / "latest" / "operations" / "runbooks" / "production-operations-baseline.md"
)
DEFAULT_CLUSTER_EVIDENCE = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "k8s-cluster-evidence.json"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "k8s-readiness-report.json"
DEFAULT_SUMMARY_OUTPUT = REPO_ROOT / "docs" / "working" / "status" / "baselines" / "k8s-readiness-summary.md"

REQUIRED_RESOURCES = {
    "Namespace": "omni-skill-pipeline",
    "ConfigMap": "omni-skill-pipeline-config",
    "Deployment": "omni-skill-pipeline",
    "Service": "omni-skill-pipeline",
    "Ingress": "omni-skill-pipeline",
    "HorizontalPodAutoscaler": "omni-skill-pipeline",
}
REQUIRED_KUSTOMIZATION_FILES = (
    "namespace.yaml",
    "configmap.yaml",
    "deployment.yaml",
    "service.yaml",
    "ingress.yaml",
    "hpa.yaml",
)
REQUIRED_KUSTOMIZATION_REFS = tuple("../%s" % name for name in REQUIRED_KUSTOMIZATION_FILES)
REQUIRED_SECRET_ENV_VARS = (
    "OPENAI_API_KEY",
    "OMNI_API_KEY",
    "OMNI_POSTGRES_REPOSITORY_DSN",
    "OMNI_ARTIFACT_ENCRYPTION_KEY",
)
REQUIRED_RUNBOOK_MARKERS = (
    "kubectl apply --dry-run=server -f k8s/",
    "kubectl rollout status deployment/omni-skill-pipeline",
    "kubectl logs deployment/omni-skill-pipeline",
    "python scripts/k8s_readiness.py",
)
SENSITIVE_NAME_RE = re.compile(r"\b(?:API_KEY|SECRET|TOKEN|PASSWORD|DSN|ENCRYPTION_KEY)\b", re.IGNORECASE)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Kubernetes manifest and rollout evidence readiness without requiring a live cluster.",
    )
    parser.add_argument("--manifest-dir", default=str(DEFAULT_MANIFEST_DIR))
    parser.add_argument("--production-ops-runbook", default=str(DEFAULT_PRODUCTION_OPS_RUNBOOK))
    parser.add_argument("--cluster-evidence", default=str(DEFAULT_CLUSTER_EVIDENCE))
    parser.add_argument(
        "--require-cluster-evidence",
        action="store_true",
        help="Require external kubectl dry-run, rollout, and log-inspection evidence.",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help='JSON report output. Use "-" to skip writing.')
    parser.add_argument("--summary-output", default=str(DEFAULT_SUMMARY_OUTPUT), help='Markdown output. Use "-" to skip.')
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--fail-on-blocked", action="store_true")
    return parser.parse_args()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _check(check_id: str, status: str, actual: Any, expected: Any, details: str = "") -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "actual": actual,
        "expected": expected,
        "details": details,
    }


def _yaml_files(manifest_dir: Path) -> list[Path]:
    files = sorted(manifest_dir.glob("*.yaml")) + sorted(manifest_dir.glob("*.yml"))
    return [path for path in files if path.is_file()]


def _document_chunks(path: Path) -> list[str]:
    return [chunk.strip() for chunk in re.split(r"(?m)^---\s*$", _read_text(path)) if chunk.strip()]


def _metadata_name(document: str) -> str:
    lines = document.splitlines()
    in_metadata = False
    for line in lines:
        if re.match(r"^metadata:\s*$", line):
            in_metadata = True
            continue
        if in_metadata and line and not line.startswith((" ", "\t")):
            return ""
        if in_metadata:
            match = re.match(r"^\s+name:\s*([A-Za-z0-9_.-]+)\s*$", line)
            if match:
                return match.group(1)
    return ""


def _resource_index(files: list[Path], root: Path) -> dict[tuple[str, str], dict[str, str]]:
    resources: dict[tuple[str, str], dict[str, str]] = {}
    for path in files:
        for document in _document_chunks(path):
            kind_match = re.search(r"(?m)^kind:\s*([A-Za-z0-9]+)\s*$", document)
            if not kind_match:
                continue
            kind = kind_match.group(1)
            name = _metadata_name(document)
            if not name:
                continue
            resources[(kind, name)] = {
                "kind": kind,
                "name": name,
                "path": str(path.relative_to(root)),
                "text": document,
            }
    return resources


def _check_required_manifest_files(manifest_dir: Path, files: list[Path]) -> dict[str, Any]:
    if not manifest_dir.is_dir():
        return _check(
            "k8s_manifest_dir",
            "fail",
            "missing",
            str(manifest_dir),
            details="Kubernetes manifest directory must exist.",
        )
    present = sorted(path.name for path in files)
    missing = [name for name in REQUIRED_KUSTOMIZATION_FILES if name not in present]
    return _check(
        "k8s_manifest_files",
        "pass" if not missing else "fail",
        {"present": present, "missing": missing},
        {"missing": []},
        details="P2 Kubernetes baseline requires deployment, service, ingress, configmap, HPA, and namespace manifests.",
    )


def _check_kustomization(manifest_dir: Path) -> dict[str, Any]:
    path = manifest_dir / "kustomize" / "kustomization.yaml"
    if not path.is_file():
        return _check("k8s_kustomization", "fail", "missing", str(path))
    text = _read_text(path)
    missing = [name for name in REQUIRED_KUSTOMIZATION_REFS if name not in text]
    return _check(
        "k8s_kustomization",
        "pass" if not missing else "fail",
        {"missing_resources": missing},
        {"missing_resources": []},
        details="kustomization.yaml must enumerate the minimal K8s deployment baseline.",
    )


def _check_required_resources(resources: dict[tuple[str, str], dict[str, str]]) -> dict[str, Any]:
    missing = [
        {"kind": kind, "name": name}
        for kind, name in REQUIRED_RESOURCES.items()
        if (kind, name) not in resources
    ]
    return _check(
        "k8s_required_resources",
        "pass" if not missing else "fail",
        {"missing": missing},
        {"missing": []},
        details="K8s baseline must include deployment, service, ingress, configmap, secret refs, probes, and HPA.",
    )


def _integer_marker(text: str, name: str) -> int:
    match = re.search(r"(?m)^\s*%s:\s*([0-9]+)\s*$" % re.escape(name), text)
    return int(match.group(1)) if match else 0


def _check_deployment_contract(resources: dict[tuple[str, str], dict[str, str]]) -> dict[str, Any]:
    deployment = resources.get(("Deployment", "omni-skill-pipeline"))
    if deployment is None:
        return _check("k8s_deployment_contract", "fail", "missing", "Deployment/omni-skill-pipeline")
    text = deployment["text"]
    missing_markers: list[str] = []
    for marker in (
        "replicas: 2",
        "containerPort: 8000",
        "readinessProbe:",
        "livenessProbe:",
        "path: /healthz",
        "secretKeyRef:",
        "resources:",
        "runAsNonRoot: true",
        "allowPrivilegeEscalation: false",
        "drop:",
        "emptyDir:",
    ):
        if marker not in text:
            missing_markers.append(marker)
    missing_secret_env = [name for name in REQUIRED_SECRET_ENV_VARS if "name: %s" % name not in text]
    if "name: omni-skill-pipeline-secrets" not in text:
        missing_markers.append("secret name omni-skill-pipeline-secrets")
    return _check(
        "k8s_deployment_contract",
        "pass" if not missing_markers and not missing_secret_env else "fail",
        {"missing_markers": missing_markers, "missing_secret_env": missing_secret_env},
        {"missing_markers": [], "missing_secret_env": []},
        details="Deployment must expose /healthz probes, use secret refs, and define basic security/resource controls.",
    )


def _check_networking_contract(resources: dict[tuple[str, str], dict[str, str]]) -> dict[str, Any]:
    service = resources.get(("Service", "omni-skill-pipeline"))
    ingress = resources.get(("Ingress", "omni-skill-pipeline"))
    missing_markers: list[str] = []
    if service is None:
        missing_markers.append("Service/omni-skill-pipeline")
    else:
        service_text = service["text"]
        for marker in ("type: ClusterIP", "port: 80", "targetPort: http"):
            if marker not in service_text:
                missing_markers.append("service %s" % marker)
    if ingress is None:
        missing_markers.append("Ingress/omni-skill-pipeline")
    else:
        ingress_text = ingress["text"]
        for marker in ("host: omni-skill-pipeline.example.com", "name: omni-skill-pipeline", "number: 80"):
            if marker not in ingress_text:
                missing_markers.append("ingress %s" % marker)
    return _check(
        "k8s_networking_contract",
        "pass" if not missing_markers else "fail",
        {"missing_markers": missing_markers},
        {"missing_markers": []},
        details="Service and ingress must route external traffic to the API service.",
    )


def _check_hpa_contract(resources: dict[tuple[str, str], dict[str, str]]) -> dict[str, Any]:
    hpa = resources.get(("HorizontalPodAutoscaler", "omni-skill-pipeline"))
    if hpa is None:
        return _check("k8s_hpa_contract", "fail", "missing", "HorizontalPodAutoscaler/omni-skill-pipeline")
    text = hpa["text"]
    min_replicas = _integer_marker(text, "minReplicas")
    max_replicas = _integer_marker(text, "maxReplicas")
    avg_cpu = _integer_marker(text, "averageUtilization")
    failure_codes: list[str] = []
    if min_replicas < 2:
        failure_codes.append("min_replicas_too_low")
    if max_replicas < 3:
        failure_codes.append("max_replicas_too_low")
    if avg_cpu <= 0:
        failure_codes.append("cpu_target_missing")
    if "kind: Deployment" not in text or "name: omni-skill-pipeline" not in text:
        failure_codes.append("deployment_target_missing")
    return _check(
        "k8s_hpa_contract",
        "pass" if not failure_codes else "fail",
        {
            "min_replicas": min_replicas,
            "max_replicas": max_replicas,
            "average_cpu_utilization": avg_cpu,
            "failure_codes": failure_codes,
        },
        {"min_replicas_min": 2, "max_replicas_min": 3, "average_cpu_utilization_gt": 0},
        details="HPA must target the API deployment and define non-trivial scale bounds.",
    )


def _placeholder(value: str) -> bool:
    text = value.strip().strip("'\"")
    if not text:
        return True
    if text.startswith("<") and text.endswith(">"):
        return True
    if text.startswith("${") or text.startswith("$("):
        return True
    return text.lower() in {"changeme", "change-me", "example", "placeholder", "dummy"}


def _check_no_plaintext_secrets(files: list[Path], root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for path in files:
        active_sensitive_name = ""
        for line_no, line in enumerate(_read_text(path).splitlines(), start=1):
            name_match = re.search(r"\bname:\s*([A-Z0-9_]+)\s*$", line)
            if name_match and SENSITIVE_NAME_RE.search(name_match.group(1)):
                active_sensitive_name = name_match.group(1)
                continue
            if active_sensitive_name and "valueFrom:" in line:
                active_sensitive_name = ""
                continue
            value_match = re.search(r"\bvalue:\s*([^#\r\n]+)", line)
            if active_sensitive_name and value_match and not _placeholder(value_match.group(1)):
                findings.append(
                    {
                        "path": str(path.relative_to(root)),
                        "line": line_no,
                        "name": active_sensitive_name,
                        "value_preview": value_match.group(1).strip()[:8],
                    }
                )
                active_sensitive_name = ""
    return _check(
        "k8s_no_plaintext_secrets",
        "pass" if not findings else "fail",
        {"findings": findings},
        {"findings": []},
        details="K8s manifests must use secretKeyRef/valueFrom for high-risk secret env vars.",
    )


def _check_runbook_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check("k8s_runbook_contract", "fail", "missing", str(path))
    text = _read_text(path)
    missing = [marker for marker in REQUIRED_RUNBOOK_MARKERS if marker not in text]
    return _check(
        "k8s_runbook_contract",
        "pass" if not missing else "fail",
        {"missing_markers": missing, "path": str(path)},
        {"missing_markers": []},
        details="Production operations runbook must explain K8s dry-run, rollout, logs, and readiness evidence.",
    )


def _status_pass(value: Any) -> bool:
    return str(value or "").strip().lower() in {"pass", "passed", "ok", "ready", "true"}


def _check_cluster_evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _check(
            "k8s_cluster_evidence",
            "fail",
            "missing",
            str(path),
            details="Live Kubernetes readiness requires external cluster evidence.",
        )
    try:
        payload = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check("k8s_cluster_evidence", "fail", str(exc), "valid JSON object")

    failure_codes: list[str] = []
    if payload.get("schema_version") != CLUSTER_EVIDENCE_SCHEMA_VERSION:
        failure_codes.append("schema_version_mismatch")
    if not _status_pass(payload.get("status")):
        failure_codes.append("status_not_pass")
    if str(payload.get("namespace", "")).strip() != "omni-skill-pipeline":
        failure_codes.append("namespace_mismatch")
    for key in (
        "server_dry_run_status",
        "rollout_status",
        "health_probe_status",
        "log_inspection_status",
        "secret_reference_status",
    ):
        if not _status_pass(payload.get(key)):
            failure_codes.append("%s_not_pass" % key)
    return _check(
        "k8s_cluster_evidence",
        "pass" if not failure_codes else "fail",
        {"failure_codes": failure_codes, "namespace": payload.get("namespace")},
        {
            "schema_version": CLUSTER_EVIDENCE_SCHEMA_VERSION,
            "namespace": "omni-skill-pipeline",
            "all_status_fields": "pass",
        },
        details="Cluster evidence must cover server dry-run, rollout, health probe, logs, and secret references.",
    )


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    manifest_dir = Path(args.manifest_dir).resolve()
    runbook_path = Path(args.production_ops_runbook).resolve()
    cluster_evidence_path = Path(args.cluster_evidence).resolve()
    files = _yaml_files(manifest_dir) if manifest_dir.is_dir() else []
    resources = _resource_index(files, manifest_dir) if files else {}

    checks = [
        _check_required_manifest_files(manifest_dir, files),
        _check_kustomization(manifest_dir),
        _check_required_resources(resources),
        _check_deployment_contract(resources),
        _check_networking_contract(resources),
        _check_hpa_contract(resources),
        _check_no_plaintext_secrets(files, manifest_dir),
        _check_runbook_contract(runbook_path),
    ]
    if bool(args.require_cluster_evidence):
        checks.append(_check_cluster_evidence(cluster_evidence_path))

    failed_checks = [check["id"] for check in checks if check.get("status") != "pass"]
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "status": "K8S_READINESS_READY" if not failed_checks else "K8S_READINESS_BLOCKED",
        "cluster_evidence_required": bool(args.require_cluster_evidence),
        "check_count": len(checks),
        "pass_count": len([check for check in checks if check.get("status") == "pass"]),
        "fail_count": len([check for check in checks if check.get("status") != "pass"]),
        "failed_checks": failed_checks,
        "checks": checks,
        "evidence_paths": {
            "manifest_dir": str(manifest_dir),
            "production_ops_runbook": str(runbook_path),
            "cluster_evidence": str(cluster_evidence_path),
        },
    }


def _render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# K8s Readiness Summary",
        "",
        "- Status: `%s`" % report.get("status", "K8S_READINESS_BLOCKED"),
        "- Cluster evidence required: `%s`" % report.get("cluster_evidence_required", False),
        "- Checks: `%s`" % report.get("check_count", 0),
        "- Passed: `%s`" % report.get("pass_count", 0),
        "- Failed: `%s`" % report.get("fail_count", 0),
        "- Failed checks: `%s`" % (", ".join(report.get("failed_checks", [])) or "none"),
        "",
        "## Check Results",
        "",
    ]
    for check in report.get("checks", []):
        lines.append("- `%s`: `%s`" % (check.get("id"), check.get("status")))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    try:
        report = _build_report(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("K8s readiness failed: %s" % exc, file=sys.stderr)
        return 2

    summary = _render_summary(report)
    output_value = str(args.output or "").strip()
    summary_output_value = str(args.summary_output or "").strip()
    if output_value and output_value != "-":
        _write_text(Path(output_value).resolve(), json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if summary_output_value and summary_output_value != "-":
        _write_text(Path(summary_output_value).resolve(), summary)

    print(
        "K8s readiness status=%s checks=%s pass=%s fail=%s"
        % (
            report.get("status", "K8S_READINESS_BLOCKED"),
            report.get("check_count", 0),
            report.get("pass_count", 0),
            report.get("fail_count", 0),
        )
    )
    if report.get("failed_checks"):
        print("Failed checks: %s" % ", ".join(report["failed_checks"]))
    else:
        print("Failed checks: none")
    if args.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.print_summary:
        print(summary.rstrip())
    if bool(args.fail_on_blocked) and report.get("status") != "K8S_READINESS_READY":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
