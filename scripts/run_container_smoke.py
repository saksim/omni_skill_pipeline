from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_IMAGE_TAG = "omni-skill-pipeline:local"
DEFAULT_CONTAINER_NAME = "omni-skill-pipeline-smoke"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18000
DEFAULT_HEALTH_TIMEOUT_SECONDS = 30.0
DEFAULT_HEALTH_INTERVAL_SECONDS = 1.0


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

    @property
    def health_url(self) -> str:
        return "http://%s:%s/healthz" % (self.host, self.host_port)


def _run(command: list[str]) -> int:
    print("Command: %s" % " ".join(command))
    try:
        completed = subprocess.run(command, check=False)
    except FileNotFoundError:
        print("Docker CLI not found in PATH.", file=sys.stderr)
        return 127
    return completed.returncode


def _run_capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    print("Command: %s" % " ".join(command))
    return subprocess.run(command, check=False, capture_output=True, text=True)


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
    )


def _print_plan(config: SmokeConfig) -> None:
    if not config.skip_build:
        print("Plan: docker build -t %s ." % config.image_tag)
    if not config.skip_run:
        print(
            "Plan: docker run --rm -d --name %s -p %s:8000 %s"
            % (config.container_name, config.host_port, config.image_tag)
        )
        print("Plan: poll %s" % config.health_url)
        print("Plan: docker logs %s" % config.container_name)
        print("Plan: docker rm -f %s" % config.container_name)


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def main() -> int:
    config = _to_config(_build_args())
    if config.skip_build and config.skip_run:
        print("No smoke actions selected.", file=sys.stderr)
        return 2

    _print_plan(config)
    if config.dry_run:
        return 0

    if not _docker_available():
        print(
            "Docker CLI not found in PATH. Install docker client in this environment or run this stage on host with docker available.",
            file=sys.stderr,
        )
        return 127

    if not config.skip_build:
        exit_code = _run(["docker", "build", "-t", config.image_tag, "."])
        if exit_code != 0:
            return exit_code

    if config.skip_run:
        return 0

    run_exit = _run(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            config.container_name,
            "-p",
            "%s:8000" % config.host_port,
            config.image_tag,
        ]
    )
    if run_exit != 0:
        return run_exit

    overall_exit = 0
    try:
        ok, payload = _poll_healthz(
            url=config.health_url,
            timeout_seconds=config.timeout_seconds,
            interval_seconds=config.interval_seconds,
        )
        if not ok:
            print("Health check timed out: %s" % payload, file=sys.stderr)
            overall_exit = 1
        else:
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                print("Health response (raw): %s" % payload)
            else:
                print("Health response (json): %s" % json.dumps(parsed, ensure_ascii=False))
    finally:
        _run(["docker", "logs", config.container_name])
        _run(["docker", "rm", "-f", config.container_name])
    return overall_exit


if __name__ == "__main__":
    raise SystemExit(main())
