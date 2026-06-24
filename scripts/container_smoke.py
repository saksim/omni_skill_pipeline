from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_IMAGE_TAG = "omni-skill-pipeline:local"
DEFAULT_CONTAINER_NAME = "omni-skill-pipeline-smoke"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18000
DEFAULT_HEALTH_TIMEOUT_SECONDS = 30.0
DEFAULT_HEALTH_INTERVAL_SECONDS = 1.0
REPORT_SCHEMA_VERSION = "container_smoke.v1"
MAX_CAPTURED_OUTPUT_CHARS = 12000


@dataclass(frozen=True)
class SmokeConfig:
    image_tag: str
    container_name: str
    host: str
    host_port: int
    timeout_seconds: float
    interval_seconds: float
    skip_build: bool
    skip_run: bool
    dry_run: bool
    docker_config_dir: str
    output_path: str
    summary_output_path: str
    print_json: bool

    @property
    def health_url(self) -> str:
        return "http://%s:%s/healthz" % (self.host, self.host_port)


def _tail_text(value: str, *, limit: int = MAX_CAPTURED_OUTPUT_CHARS) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def _run_capture(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    print("Command: %s" % " ".join(command))
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            args=command,
            returncode=127,
            stdout="",
            stderr="Docker CLI not found in PATH.\n",
        )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed


def _poll_healthz(url: str, timeout_seconds: float, interval_seconds: float) -> tuple[bool, str]:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() <= deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                body = response.read().decode("utf-8", errors="ignore")
                status_code = getattr(response, "status", 0)
                if status_code in (200, 503):
                    return True, body
                last_error = "status=%s body=%s" % (status_code, body)
        except urllib.error.URLError as exc:
            last_error = str(exc)
        except Exception as exc:
            last_error = str(exc)
        time.sleep(max(interval_seconds, 0.1))
    return False, last_error


def _build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Docker image and smoke-check API /healthz for the container baseline.",
    )
    parser.add_argument("--image-tag", default=DEFAULT_IMAGE_TAG, help="Image tag to build/run.")
    parser.add_argument("--container-name", default=DEFAULT_CONTAINER_NAME, help="Container name for smoke run.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host used for health check URL.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Host port mapped to container 8000.")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_HEALTH_TIMEOUT_SECONDS,
        help="Health polling timeout seconds.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=DEFAULT_HEALTH_INTERVAL_SECONDS,
        help="Health polling interval seconds.",
    )
    parser.add_argument("--skip-build", action="store_true", help="Skip docker build step.")
    parser.add_argument("--skip-run", action="store_true", help="Skip docker run + health check step.")
    parser.add_argument("--dry-run", action="store_true", help="Print plan only.")
    parser.add_argument(
        "--docker-config-dir",
        default="",
        help="Optional Docker config directory for environments whose default ~/.docker is not readable.",
    )
    parser.add_argument("--output", default="", help="Optional JSON report output path.")
    parser.add_argument("--summary-output", default="", help="Optional Markdown summary output path.")
    parser.add_argument("--print-json", action="store_true", help="Print the structured smoke report JSON.")
    return parser.parse_args()


def _to_config(args: argparse.Namespace) -> SmokeConfig:
    return SmokeConfig(
        image_tag=str(args.image_tag).strip() or DEFAULT_IMAGE_TAG,
        container_name=str(args.container_name).strip() or DEFAULT_CONTAINER_NAME,
        host=str(args.host).strip() or DEFAULT_HOST,
        host_port=max(int(args.port), 1),
        timeout_seconds=max(float(args.timeout_seconds), 1.0),
        interval_seconds=max(float(args.interval_seconds), 0.1),
        skip_build=bool(args.skip_build),
        skip_run=bool(args.skip_run),
        dry_run=bool(args.dry_run),
        docker_config_dir=str(args.docker_config_dir).strip(),
        output_path=str(args.output).strip(),
        summary_output_path=str(args.summary_output).strip(),
        print_json=bool(args.print_json),
    )


def _print_plan(config: SmokeConfig) -> None:
    if not config.skip_build:
        print("Plan: docker build -t %s ." % config.image_tag)
    print("Plan: docker image inspect %s --format {{.Size}}" % config.image_tag)
    if not config.skip_run:
        print("Plan: docker run --rm %s omni-skill --help" % config.image_tag)
        print(
            "Plan: docker run -d --name %s -p %s:8000 %s"
            % (config.container_name, config.host_port, config.image_tag)
        )
        print("Plan: poll %s" % config.health_url)
        print("Plan: docker logs %s" % config.container_name)
        print("Plan: docker rm -f %s" % config.container_name)


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _docker_env(config: SmokeConfig) -> dict[str, str]:
    env = os.environ.copy()
    if config.docker_config_dir:
        docker_config_dir = Path(config.docker_config_dir).expanduser().resolve()
        docker_config_dir.mkdir(parents=True, exist_ok=True)
        env["DOCKER_CONFIG"] = str(docker_config_dir)
    return env


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _command_string(command: list[str]) -> str:
    return " ".join(command)


def _build_command(config: SmokeConfig) -> list[str]:
    return ["docker", "build", "-t", config.image_tag, "."]


def _image_size_command(config: SmokeConfig) -> list[str]:
    return ["docker", "image", "inspect", config.image_tag, "--format", "{{.Size}}"]


def _cli_smoke_command(config: SmokeConfig) -> list[str]:
    return ["docker", "run", "--rm", config.image_tag, "omni-skill", "--help"]


def _run_command(config: SmokeConfig) -> list[str]:
    return [
        "docker",
        "run",
        "-d",
        "--name",
        config.container_name,
        "-p",
        "%s:8000" % config.host_port,
        config.image_tag,
    ]


def _logs_command(config: SmokeConfig) -> list[str]:
    return ["docker", "logs", config.container_name]


def _cleanup_command(config: SmokeConfig) -> list[str]:
    return ["docker", "rm", "-f", config.container_name]


def _new_report(config: SmokeConfig) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "decision": "PENDING",
        "failure_stage": "",
        "failure_category": "",
        "failure_message": "",
        "config": {
            "image_tag": config.image_tag,
            "container_name": config.container_name,
            "host": config.host,
            "host_port": config.host_port,
            "health_url": config.health_url,
            "timeout_seconds": config.timeout_seconds,
            "interval_seconds": config.interval_seconds,
            "skip_build": config.skip_build,
            "skip_run": config.skip_run,
            "dry_run": config.dry_run,
            "docker_config_dir": str(Path(config.docker_config_dir).expanduser().resolve())
            if config.docker_config_dir
            else "",
        },
        "commands": {
            "build": _build_command(config),
            "image_size": _image_size_command(config),
            "cli_smoke": _cli_smoke_command(config),
            "run": _run_command(config),
            "logs": _logs_command(config),
            "cleanup": _cleanup_command(config),
        },
        "image": {
            "size_bytes": None,
        },
        "stages": [],
    }


def _record_stage(
    report: dict[str, Any],
    *,
    name: str,
    status: str,
    command: list[str] | None = None,
    returncode: int | None = None,
    stdout: str = "",
    stderr: str = "",
    message: str = "",
    category: str = "",
    details: dict[str, Any] | None = None,
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
        stage["command_string"] = _command_string(command)
    if returncode is not None:
        stage["returncode"] = int(returncode)
    if stdout:
        stage["stdout_tail"] = _tail_text(stdout)
    if stderr:
        stage["stderr_tail"] = _tail_text(stderr)
    if details:
        stage["details"] = details
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


def _classify_build_failure(stderr: str) -> str:
    normalized = stderr.lower()
    if "load metadata for" in normalized and (
        "failed to fetch anonymous token" in normalized
        or "failed to fetch oauth token" in normalized
        or "failed to authorize" in normalized
    ):
        return "docker_base_image_pull_failed"
    return "docker_build_failed"


def _write_json(path_value: str, payload: dict[str, Any]) -> None:
    if not path_value:
        return
    path = Path(path_value).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _render_summary(report: dict[str, Any]) -> str:
    config = report.get("config", {})
    image = report.get("image", {})
    if not isinstance(image, dict):
        image = {}
    stages = report.get("stages", [])
    if not isinstance(stages, list):
        stages = []
    lines = [
        "# Container Smoke Summary",
        "",
        "- Decision: `%s`" % str(report.get("decision", "PENDING")),
        "- Failure stage: `%s`" % str(report.get("failure_stage", "")),
        "- Failure category: `%s`" % str(report.get("failure_category", "")),
        "- Image tag: `%s`" % str(config.get("image_tag", "")),
        "- Image size bytes: `%s`" % str(image.get("size_bytes", "")),
        "- Container name: `%s`" % str(config.get("container_name", "")),
        "- Health URL: `%s`" % str(config.get("health_url", "")),
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


def main() -> int:
    config = _to_config(_build_args())
    report = _new_report(config)
    if config.skip_build and config.skip_run:
        _record_stage(
            report,
            name="config",
            status="fail",
            message="No smoke actions selected.",
            category="no_smoke_actions_selected",
        )
        _set_decision(
            report,
            "FAIL",
            failure_stage="config",
            failure_category="no_smoke_actions_selected",
            failure_message="No smoke actions selected.",
        )
        _emit_outputs(config, report)
        print("No smoke actions selected.", file=sys.stderr)
        return 2

    _print_plan(config)
    if config.dry_run:
        _record_stage(report, name="plan", status="pass", message="Dry-run plan generated.")
        _set_decision(report, "DRY_RUN")
        _emit_outputs(config, report)
        return 0

    if not _docker_available():
        _record_stage(
            report,
            name="docker_cli",
            status="fail",
            message="Docker CLI not found in PATH.",
            category="docker_cli_missing",
        )
        _set_decision(
            report,
            "FAIL",
            failure_stage="docker_cli",
            failure_category="docker_cli_missing",
            failure_message="Docker CLI not found in PATH.",
        )
        _emit_outputs(config, report)
        print(
            "Docker CLI not found in PATH. Install docker client in this environment or run this stage on host with docker available.",
            file=sys.stderr,
        )
        return 127

    env = _docker_env(config)
    _record_stage(report, name="docker_cli", status="pass", message="Docker CLI found in PATH.")
    daemon_command = ["docker", "info"]
    daemon = _run_capture(daemon_command, env=env)
    if daemon.returncode != 0:
        message = "Docker daemon is not reachable."
        _record_stage(
            report,
            name="docker_daemon",
            status="fail",
            command=daemon_command,
            returncode=daemon.returncode,
            stdout=daemon.stdout,
            stderr=daemon.stderr,
            message=message,
            category="docker_daemon_unavailable",
        )
        _set_decision(
            report,
            "FAIL",
            failure_stage="docker_daemon",
            failure_category="docker_daemon_unavailable",
            failure_message=message,
        )
        _emit_outputs(config, report)
        return daemon.returncode or 125
    _record_stage(
        report,
        name="docker_daemon",
        status="pass",
        command=daemon_command,
        returncode=daemon.returncode,
        stdout=daemon.stdout,
        stderr=daemon.stderr,
        message="Docker daemon is reachable.",
    )

    if not config.skip_build:
        build_command = _build_command(config)
        build = _run_capture(build_command, env=env)
        if build.returncode != 0:
            failure_category = _classify_build_failure(build.stderr)
            message = (
                "Docker image build failed while pulling base image metadata."
                if failure_category == "docker_base_image_pull_failed"
                else "Docker image build failed."
            )
            _record_stage(
                report,
                name="image_build",
                status="fail",
                command=build_command,
                returncode=build.returncode,
                stdout=build.stdout,
                stderr=build.stderr,
                message=message,
                category=failure_category,
            )
            _set_decision(
                report,
                "FAIL",
                failure_stage="image_build",
                failure_category=failure_category,
                failure_message=message,
            )
            _emit_outputs(config, report)
            return build.returncode
        _record_stage(
            report,
            name="image_build",
            status="pass",
            command=build_command,
            returncode=build.returncode,
            stdout=build.stdout,
            stderr=build.stderr,
            message="Docker image build completed.",
        )
    else:
        _record_stage(report, name="image_build", status="skipped", message="--skip-build was set.")

    image_size_command = _image_size_command(config)
    image_size = _run_capture(image_size_command, env=env)
    image_size_text = image_size.stdout.strip().splitlines()[-1] if image_size.stdout.strip() else ""
    try:
        image_size_bytes = int(image_size_text)
    except ValueError:
        image_size_bytes = -1
    if image_size.returncode != 0 or image_size_bytes < 0:
        message = "Docker image size inspection failed."
        _record_stage(
            report,
            name="image_size",
            status="fail",
            command=image_size_command,
            returncode=image_size.returncode,
            stdout=image_size.stdout,
            stderr=image_size.stderr,
            message=message,
            category="docker_image_size_inspect_failed",
        )
        _set_decision(
            report,
            "FAIL",
            failure_stage="image_size",
            failure_category="docker_image_size_inspect_failed",
            failure_message=message,
        )
        _emit_outputs(config, report)
        return image_size.returncode or 125
    report["image"]["size_bytes"] = image_size_bytes
    _record_stage(
        report,
        name="image_size",
        status="pass",
        command=image_size_command,
        returncode=image_size.returncode,
        stdout=image_size.stdout,
        stderr=image_size.stderr,
        message="Docker image size recorded.",
        details={"image_size_bytes": image_size_bytes},
    )

    if config.skip_run:
        _record_stage(report, name="container_run", status="skipped", message="--skip-run was set.")
        _record_stage(report, name="cli_smoke", status="skipped", message="--skip-run was set.")
        _record_stage(report, name="healthz", status="skipped", message="--skip-run was set.")
        _set_decision(report, "PASS")
        _emit_outputs(config, report)
        return 0

    cli_smoke_command = _cli_smoke_command(config)
    cli_smoke = _run_capture(cli_smoke_command, env=env)
    if cli_smoke.returncode != 0:
        message = "Container CLI smoke failed."
        _record_stage(
            report,
            name="cli_smoke",
            status="fail",
            command=cli_smoke_command,
            returncode=cli_smoke.returncode,
            stdout=cli_smoke.stdout,
            stderr=cli_smoke.stderr,
            message=message,
            category="container_cli_smoke_failed",
        )
        _set_decision(
            report,
            "FAIL",
            failure_stage="cli_smoke",
            failure_category="container_cli_smoke_failed",
            failure_message=message,
        )
        _emit_outputs(config, report)
        return cli_smoke.returncode
    _record_stage(
        report,
        name="cli_smoke",
        status="pass",
        command=cli_smoke_command,
        returncode=cli_smoke.returncode,
        stdout=cli_smoke.stdout,
        stderr=cli_smoke.stderr,
        message="Container CLI smoke completed.",
    )

    run_command = _run_command(config)
    run = _run_capture(run_command, env=env)
    if run.returncode != 0:
        message = "Docker container run failed."
        _record_stage(
            report,
            name="container_run",
            status="fail",
            command=run_command,
            returncode=run.returncode,
            stdout=run.stdout,
            stderr=run.stderr,
            message=message,
            category="docker_run_failed",
        )
        _set_decision(
            report,
            "FAIL",
            failure_stage="container_run",
            failure_category="docker_run_failed",
            failure_message=message,
        )
        _emit_outputs(config, report)
        return run.returncode
    _record_stage(
        report,
        name="container_run",
        status="pass",
        command=run_command,
        returncode=run.returncode,
        stdout=run.stdout,
        stderr=run.stderr,
        message="Docker container started.",
    )

    overall_exit = 0
    try:
        ok, payload = _poll_healthz(
            url=config.health_url,
            timeout_seconds=config.timeout_seconds,
            interval_seconds=config.interval_seconds,
        )
        if not ok:
            print("Health check timed out: %s" % payload, file=sys.stderr)
            _record_stage(
                report,
                name="healthz",
                status="fail",
                message="Health check timed out: %s" % payload,
                category="health_check_failed",
            )
            _set_decision(
                report,
                "FAIL",
                failure_stage="healthz",
                failure_category="health_check_failed",
                failure_message="Health check timed out.",
            )
            overall_exit = 1
        else:
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                print("Health response (raw): %s" % payload)
                _record_stage(
                    report,
                    name="healthz",
                    status="pass",
                    message="Health endpoint returned non-JSON success payload.",
                    stdout=payload,
                )
                _set_decision(report, "PASS")
            else:
                print("Health response (json): %s" % json.dumps(parsed, ensure_ascii=False))
                _record_stage(
                    report,
                    name="healthz",
                    status="pass",
                    message="Health endpoint returned JSON payload.",
                    stdout=json.dumps(parsed, ensure_ascii=False),
                )
                _set_decision(report, "PASS")
    finally:
        logs_command = _logs_command(config)
        logs = _run_capture(logs_command, env=env)
        _record_stage(
            report,
            name="container_logs",
            status="pass" if logs.returncode == 0 else "fail",
            command=logs_command,
            returncode=logs.returncode,
            stdout=logs.stdout,
            stderr=logs.stderr,
            message="Container logs captured." if logs.returncode == 0 else "Container logs command failed.",
        )
        cleanup_command = _cleanup_command(config)
        cleanup = _run_capture(cleanup_command, env=env)
        _record_stage(
            report,
            name="cleanup",
            status="pass" if cleanup.returncode == 0 else "fail",
            command=cleanup_command,
            returncode=cleanup.returncode,
            stdout=cleanup.stdout,
            stderr=cleanup.stderr,
            message="Container removed." if cleanup.returncode == 0 else "Container cleanup command failed.",
        )
        _emit_outputs(config, report)
    return overall_exit


if __name__ == "__main__":
    raise SystemExit(main())
