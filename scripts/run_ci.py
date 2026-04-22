from __future__ import annotations

import argparse
import subprocess
import sys


def _run(command: list[str]) -> int:
    print("Command: %s" % " ".join(command))
    completed = subprocess.run(command, check=False)
    return completed.returncode


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the repository CI test checks locally.",
    )
    parser.add_argument(
        "--skip-full-suite",
        action="store_true",
        help="Skip unittest discovery across tests/test_*.py.",
    )
    parser.add_argument(
        "--skip-tp-suite",
        action="store_true",
        help="Skip the TP registry regression suite.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    commands: list[list[str]] = []
    if not args.skip_full_suite:
        commands.append([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
    if not args.skip_tp_suite:
        commands.append([sys.executable, "scripts/run_tp_tests.py", "--all", "--python", sys.executable])

    if not commands:
        print("No CI checks selected.", file=sys.stderr)
        return 2

    for command in commands:
        exit_code = _run(command)
        if exit_code != 0:
            return exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
