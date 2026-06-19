from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_SCHEMA_VERSION = "release_consumer_smoke.v1"
MAX_CAPTURED_OUTPUT_CHARS = 12000


@dataclass(frozen=True)
class SmokeConfig:
    release_dir: Path
    expected_release_id: str
    python: str
    install_mode: str
    output_path: str
    summary_output_path: str
    print_json: bool


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a GitHub Release artifact pack from a consumer point of view.",
    )
    parser.add_argument("--release-dir", required=True, help="Directory containing downloaded release assets.")
    parser.add_argument("--expected-release-id", default="", help="Expected release id/tag in release-manifest.json.")
    parser.add_argument("--python", default=sys.executable, help="Python executable used for install smoke.")
    parser.add_argument(
        "--install-mode",
        choices=["target", "none"],
        default="target",
        help="target installs the wheel into a temp target and runs CLI smoke; none skips install.",
    )
    parser.add_argument("--output", default="", help="Optional JSON report output path.")
    parser.add_argument("--summary-output", default="", help="Optional Markdown summary output path.")
    parser.add_argument("--print-json", action="store_true", help="Print JSON report.")
    return parser


def _to_config(args: argparse.Namespace) -> SmokeConfig:
    return SmokeConfig(
        release_dir=Path(str(args.release_dir)).expanduser().resolve(),
        expected_release_id=str(args.expected_release_id or "").strip(),
        python=str(args.python or sys.executable).strip() or sys.executable,
        install_mode=str(args.install_mode or "target").strip(),
        output_path=str(args.output or "").strip(),
        summary_output_path=str(args.summary_output or "").strip(),
        print_json=bool(args.print_json),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _tail_text(value: str, *, limit: int = MAX_CAPTURED_OUTPUT_CHARS) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_stage(
    report: dict[str, Any],
    *,
    name: str,
    status: str,
    message: str,
    category: str = "",
    command: list[str] | None = None,
    returncode: int | None = None,
    stdout: str = "",
    stderr: str = "",
) -> None:
    stage: dict[str, Any] = {
        "name": name,
        "status": status,
        "message": message,
    }
    if category:
        stage["category"] = category
    if command is not None:
        stage["command"] = command
        stage["command_string"] = " ".join(command)
    if returncode is not None:
        stage["returncode"] = int(returncode)
    if stdout:
        stage["stdout_tail"] = _tail_text(stdout)
    if stderr:
        stage["stderr_tail"] = _tail_text(stderr)
    report.setdefault("stages", []).append(stage)


def _set_decision(
    report: dict[str, Any],
    decision: str,
    *,
    failure_stage: str = "",
    failure_category: str = "",
    failure_message: str = "",
) -> None:
    report["decision"] = decision
    report["failure_stage"] = failure_stage
    report["failure_category"] = failure_category
    report["failure_message"] = failure_message


def _new_report(config: SmokeConfig) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "decision": "PENDING",
        "failure_stage": "",
        "failure_category": "",
        "failure_message": "",
        "config": {
            "release_dir": str(config.release_dir),
            "expected_release_id": config.expected_release_id,
            "python": config.python,
            "install_mode": config.install_mode,
        },
        "release": {},
        "stages": [],
    }


def _parse_sha256sums(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        parts = text.split(None, 1)
        if len(parts) != 2:
            raise ValueError("invalid SHA256SUMS row: %s" % line)
        digest, filename = parts
        filename = filename.strip().lstrip("*")
        if len(digest) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in digest):
            raise ValueError("invalid SHA256 digest for %s" % filename)
        if not filename:
            raise ValueError("missing filename in SHA256SUMS row")
        rows.append((digest.lower(), filename))
    if not rows:
        raise ValueError("SHA256SUMS is empty")
    return rows


def _verify_checksums(config: SmokeConfig, report: dict[str, Any]) -> bool:
    sums_path = config.release_dir / "SHA256SUMS"
    if not sums_path.is_file():
        _record_stage(
            report,
            name="sha256sums",
            status="fail",
            category="sha256sums_missing",
            message="SHA256SUMS is missing.",
        )
        return False
    try:
        rows = _parse_sha256sums(sums_path)
    except ValueError as exc:
        _record_stage(
            report,
            name="sha256sums",
            status="fail",
            category="sha256sums_invalid",
            message=str(exc),
        )
        return False

    failures: list[str] = []
    for expected, filename in rows:
        target = config.release_dir / filename
        if not target.is_file():
            failures.append("%s missing" % filename)
            continue
        actual = _sha256(target)
        if actual != expected:
            failures.append("%s digest mismatch" % filename)

    if failures:
        _record_stage(
            report,
            name="sha256sums",
            status="fail",
            category="sha256_mismatch",
            message="; ".join(failures),
        )
        return False

    _record_stage(
        report,
        name="sha256sums",
        status="pass",
        message="Verified %s checksum rows." % len(rows),
    )
    return True


def _load_manifest(config: SmokeConfig, report: dict[str, Any]) -> dict[str, Any] | None:
    path = config.release_dir / "release-manifest.json"
    if not path.is_file():
        _record_stage(
            report,
            name="manifest",
            status="fail",
            category="manifest_missing",
            message="release-manifest.json is missing.",
        )
        return None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _record_stage(
            report,
            name="manifest",
            status="fail",
            category="manifest_invalid_json",
            message=str(exc),
        )
        return None
    if not isinstance(manifest, dict):
        _record_stage(
            report,
            name="manifest",
            status="fail",
            category="manifest_invalid_shape",
            message="release-manifest.json must contain an object.",
        )
        return None
    return manifest


def _verify_manifest(config: SmokeConfig, report: dict[str, Any]) -> dict[str, Any] | None:
    manifest = _load_manifest(config, report)
    if manifest is None:
        return None

    release_id = str(manifest.get("release_id", "")).strip()
    project = manifest.get("project") if isinstance(manifest.get("project"), dict) else {}
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), list) else []
    report["release"] = {
        "release_id": release_id,
        "project_name": str(project.get("name", "")).strip(),
        "project_version": str(project.get("version", "")).strip(),
        "artifact_count": len(artifacts),
    }

    failures: list[str] = []
    if manifest.get("schema_version") != "omni.release_artifacts.v1":
        failures.append("unexpected schema_version")
    if config.expected_release_id and release_id != config.expected_release_id:
        failures.append("release_id %s does not match expected %s" % (release_id, config.expected_release_id))
    if not project.get("name") or not project.get("version"):
        failures.append("project name/version missing")

    roles: set[str] = set()
    for item in artifacts:
        if not isinstance(item, dict):
            failures.append("artifact entry is not an object")
            continue
        relative_path = str(item.get("path", "")).strip()
        role = str(item.get("role", "")).strip()
        expected_digest = str(item.get("sha256", "")).strip().lower()
        roles.add(role)
        if not relative_path:
            failures.append("artifact path missing")
            continue
        target = config.release_dir / relative_path
        if not target.is_file():
            failures.append("%s missing" % relative_path)
            continue
        if expected_digest and _sha256(target) != expected_digest:
            failures.append("%s manifest digest mismatch" % relative_path)

    for required_role in ("source_archive", "python_wheel"):
        if required_role not in roles:
            failures.append("required artifact role missing: %s" % required_role)

    if failures:
        _record_stage(
            report,
            name="manifest",
            status="fail",
            category="manifest_contract_failed",
            message="; ".join(failures),
        )
        return None

    _record_stage(
        report,
        name="manifest",
        status="pass",
        message="Manifest contract passed for release %s." % release_id,
    )
    return manifest


def _find_wheel(config: SmokeConfig) -> Path | None:
    wheels = sorted(config.release_dir.glob("*.whl"))
    if not wheels:
        return None
    return wheels[0]


def _run_capture(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(command, 127, "", "command not found: %s\n" % command[0])


def _run_install_smoke(config: SmokeConfig, report: dict[str, Any]) -> bool:
    if config.install_mode == "none":
        _record_stage(report, name="install_smoke", status="skipped", message="--install-mode none was set.")
        return True

    wheel_path = _find_wheel(config)
    if wheel_path is None:
        _record_stage(
            report,
            name="install_smoke",
            status="fail",
            category="wheel_missing",
            message="No wheel asset found.",
        )
        return False

    with tempfile.TemporaryDirectory(prefix="omni-release-consumer-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        target_dir = tmp_path / "install"
        install_command = [
            config.python,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(target_dir),
            str(wheel_path),
        ]
        install = _run_capture(install_command, cwd=tmp_path)
        if install.returncode != 0:
            _record_stage(
                report,
                name="install_wheel",
                status="fail",
                category="wheel_install_failed",
                command=install_command,
                returncode=install.returncode,
                stdout=install.stdout,
                stderr=install.stderr,
                message="Wheel install failed.",
            )
            return False
        _record_stage(
            report,
            name="install_wheel",
            status="pass",
            command=install_command,
            returncode=install.returncode,
            stdout=install.stdout,
            stderr=install.stderr,
            message="Wheel installed into isolated target.",
        )

        env = os.environ.copy()
        env["PYTHONPATH"] = str(target_dir)
        cli_command = [config.python, "-m", "omni_skill_pipeline.cli", "show-template"]
        cli = _run_capture(cli_command, cwd=tmp_path, env=env)
        if cli.returncode != 0:
            _record_stage(
                report,
                name="cli_show_template",
                status="fail",
                category="installed_cli_failed",
                command=cli_command,
                returncode=cli.returncode,
                stdout=cli.stdout,
                stderr=cli.stderr,
                message="Installed CLI show-template failed.",
            )
            return False
        if "SKILL.template.md" not in cli.stdout or "{{name}}" not in cli.stdout:
            _record_stage(
                report,
                name="cli_show_template",
                status="fail",
                category="installed_cli_unexpected_output",
                command=cli_command,
                returncode=cli.returncode,
                stdout=cli.stdout,
                stderr=cli.stderr,
                message="Installed CLI output did not include expected template markers.",
            )
            return False
        _record_stage(
            report,
            name="cli_show_template",
            status="pass",
            command=cli_command,
            returncode=cli.returncode,
            stdout=cli.stdout,
            stderr=cli.stderr,
            message="Installed CLI can read packaged skill template.",
        )
        return True


def run_smoke(config: SmokeConfig) -> dict[str, Any]:
    report = _new_report(config)
    if not config.release_dir.is_dir():
        _record_stage(
            report,
            name="release_dir",
            status="fail",
            category="release_dir_missing",
            message="Release directory is missing: %s" % config.release_dir,
        )
        _set_decision(
            report,
            "FAIL",
            failure_stage="release_dir",
            failure_category="release_dir_missing",
            failure_message="Release directory is missing.",
        )
        return report

    checksum_ok = _verify_checksums(config, report)
    manifest = _verify_manifest(config, report)
    install_ok = _run_install_smoke(config, report) if checksum_ok and manifest is not None else False

    if checksum_ok and manifest is not None and install_ok:
        _set_decision(report, "PASS")
    else:
        failed_stage = next((stage for stage in report.get("stages", []) if stage.get("status") == "fail"), {})
        _set_decision(
            report,
            "FAIL",
            failure_stage=str(failed_stage.get("name", "")),
            failure_category=str(failed_stage.get("category", "")),
            failure_message=str(failed_stage.get("message", "")),
        )
    return report


def _write_json(path_value: str, payload: dict[str, Any]) -> None:
    if not path_value:
        return
    path = Path(path_value).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _render_summary(report: dict[str, Any]) -> str:
    release = report.get("release") if isinstance(report.get("release"), dict) else {}
    stages = report.get("stages") if isinstance(report.get("stages"), list) else []
    lines = [
        "# Release Consumer Smoke Summary",
        "",
        "- Decision: `%s`" % str(report.get("decision", "")),
        "- Release id: `%s`" % str(release.get("release_id", "")),
        "- Project: `%s`" % str(release.get("project_name", "")),
        "- Version: `%s`" % str(release.get("project_version", "")),
        "- Failure stage: `%s`" % str(report.get("failure_stage", "")),
        "- Failure category: `%s`" % str(report.get("failure_category", "")),
        "",
        "## Stages",
        "",
    ]
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        lines.append(
            "- `%s`: `%s`%s"
            % (
                str(stage.get("name", "")),
                str(stage.get("status", "")),
                " - %s" % str(stage.get("message", "")) if str(stage.get("message", "")) else "",
            )
        )
    lines.append("")
    return "\n".join(lines)


def _emit_outputs(config: SmokeConfig, report: dict[str, Any]) -> None:
    _write_json(config.output_path, report)
    if config.summary_output_path:
        summary_path = Path(config.summary_output_path).expanduser().resolve()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(_render_summary(report), encoding="utf-8")
    if config.print_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    config = _to_config(_build_parser().parse_args(argv))
    report = run_smoke(config)
    _emit_outputs(config, report)
    return 0 if report.get("decision") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
