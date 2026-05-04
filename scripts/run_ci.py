from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys

DEFAULT_COVERAGE_FAIL_UNDER = 50.0
DEFAULT_COVERAGE_XML_PATH = "coverage.xml"


def _run(command: list[str]) -> int:
    print("Command: %s" % " ".join(command))
    completed = subprocess.run(command, check=False)
    return completed.returncode


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the repository CI test checks locally.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help='Python command used to run checks. Supports args, e.g. --python "python3.11".',
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
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage collection and fail-under gate.",
    )
    parser.add_argument(
        "--coverage-fail-under",
        type=float,
        default=DEFAULT_COVERAGE_FAIL_UNDER,
        help="Coverage fail-under threshold (default: %(default)s).",
    )
    parser.add_argument(
        "--coverage-xml",
        default=DEFAULT_COVERAGE_XML_PATH,
        help="Coverage XML output path (default: %(default)s).",
    )
    parser.add_argument(
        "--skip-coverage-xml",
        action="store_true",
        help="Skip generating coverage XML output.",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue running selected checks after failures and summarize all failed commands.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    coverage_enabled = not args.no_coverage
    python_cmd = shlex.split(args.python, posix=os.name != "nt")
    if not python_cmd:
        print("Empty --python command.", file=sys.stderr)
        return 2

    if coverage_enabled and args.skip_full_suite:
        print(
            "Coverage requires the full suite. Use --no-coverage when passing --skip-full-suite.",
            file=sys.stderr,
        )
        return 2

    commands: list[list[str]] = []
    if not args.skip_full_suite:
        if coverage_enabled:
            commands.append(
                [
                    *python_cmd,
                    "-m",
                    "coverage",
                    "run",
                    "--parallel-mode",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_*.py",
                ]
            )
        else:
            commands.append([*python_cmd, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
    if not args.skip_tp_suite:
        commands.append([*python_cmd, "scripts/run_tp_tests.py", "--all", "--python", args.python])

    if not commands:
        print("No CI checks selected.", file=sys.stderr)
        return 2

    failures: list[tuple[str, int]] = []

    if coverage_enabled:
        exit_code = _run([*python_cmd, "-m", "coverage", "erase"])
        if exit_code != 0:
            failures.append(("coverage_erase", exit_code))
            if not args.keep_going:
                return exit_code

    for command in commands:
        exit_code = _run(command)
        if exit_code != 0:
            failures.append((" ".join(command), exit_code))
            if not args.keep_going:
                return exit_code

    if coverage_enabled:
        post_commands: list[list[str]] = [
            [*python_cmd, "-m", "coverage", "combine"],
            [
                *python_cmd,
                "-m",
                "coverage",
                "report",
                "--show-missing",
                "--fail-under",
                str(args.coverage_fail_under),
            ],
        ]
        if not args.skip_coverage_xml:
            post_commands.append([*python_cmd, "-m", "coverage", "xml", "-o", args.coverage_xml])
        for command in post_commands:
            exit_code = _run(command)
            if exit_code != 0:
                failures.append((" ".join(command), exit_code))
                if not args.keep_going:
                    return exit_code
    if failures:
        print("CI failures summary:", file=sys.stderr)
        for label, exit_code in failures:
            print("- %s (exit=%s)" % (label, exit_code), file=sys.stderr)
        return failures[0][1]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
