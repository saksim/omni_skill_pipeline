from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

DEFAULT_COVERAGE_FAIL_UNDER = 50.0
DEFAULT_COVERAGE_XML_PATH = "coverage.xml"
DEFAULT_TESTS_DIR = "tests"
DEFAULT_TEST_PATTERN = "test_*.py"
COVERAGE_ENV_KEYS = (
    "COVERAGE_PROCESS_START",
    "COVERAGE_RCFILE",
    "COV_CORE_CONFIG",
    "COV_CORE_DATAFILE",
    "COV_CORE_SOURCE",
)


def _split_python_command(command: str) -> list[str]:
    parts = shlex.split(command, posix=os.name != "nt")
    if os.name == "nt":
        parts = [
            part[1:-1]
            if len(part) >= 2 and part[0] == part[-1] and part[0] in ("'", '"')
            else part
            for part in parts
        ]
    return parts


def _run(command: list[str], *, env: dict[str, str] | None = None) -> int:
    print("Command: %s" % " ".join(command))
    completed = subprocess.run(command, check=False, env=env)
    return completed.returncode


def _is_docker_runtime() -> bool:
    return Path("/.dockerenv").exists()


def _coverage_data_files() -> list[Path]:
    cwd = Path.cwd()
    return sorted(
        item
        for item in cwd.iterdir()
        if item.is_file() and (item.name == ".coverage" or item.name.startswith(".coverage."))
    )


def _discover_test_files(tests_dir: str, test_pattern: str) -> list[Path]:
    root = Path(tests_dir)
    if not root.is_dir():
        return []
    return sorted(path for path in root.glob(test_pattern) if path.is_file())


def _ci_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in COVERAGE_ENV_KEYS:
        env.pop(key, None)
    return env


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
        "--tests-dir",
        default=DEFAULT_TESTS_DIR,
        help="Directory containing unittest files (default: %(default)s).",
    )
    parser.add_argument(
        "--test-pattern",
        default=DEFAULT_TEST_PATTERN,
        help="Unittest file glob for discovery/isolation (default: %(default)s).",
    )
    parser.add_argument(
        "--isolate-test-files",
        dest="isolate_test_files",
        action="store_true",
        default=None,
        help="Run each tests/test_*.py file in a separate process.",
    )
    parser.add_argument(
        "--no-isolate-test-files",
        dest="isolate_test_files",
        action="store_false",
        help="Force legacy single-process unittest discovery, even inside Docker.",
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
    python_cmd = _split_python_command(args.python)
    if not python_cmd:
        print("Empty --python command.", file=sys.stderr)
        return 2

    if coverage_enabled and args.skip_full_suite:
        print(
            "Coverage requires the full suite. Use --no-coverage when passing --skip-full-suite.",
            file=sys.stderr,
        )
        return 2

    isolate_test_files = bool(args.isolate_test_files)
    if args.isolate_test_files is None:
        isolate_test_files = _is_docker_runtime()

    commands: list[list[str]] = []
    if not args.skip_full_suite:
        if isolate_test_files:
            test_files = _discover_test_files(str(args.tests_dir), str(args.test_pattern))
            if not test_files:
                print(
                    "No unittest files matched %s/%s." % (args.tests_dir, args.test_pattern),
                    file=sys.stderr,
                )
                return 2
            print("CI unittest mode: isolated files (%s files)" % len(test_files))
            for test_file in test_files:
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
                            str(test_file),
                        ]
                    )
                else:
                    commands.append([*python_cmd, "-m", "unittest", str(test_file)])
        else:
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
                        str(args.tests_dir),
                        "-p",
                        str(args.test_pattern),
                    ]
                )
            else:
                commands.append(
                    [
                        *python_cmd,
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        str(args.tests_dir),
                        "-p",
                        str(args.test_pattern),
                    ]
                )
    if not args.skip_tp_suite:
        commands.append([*python_cmd, "scripts/tp_tests.py", "--all", "--python", args.python])

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

    command_env = _ci_subprocess_env()
    for command in commands:
        exit_code = _run(command, env=command_env)
        if exit_code != 0:
            failures.append((" ".join(command), exit_code))
            if not args.keep_going:
                return exit_code

    if coverage_enabled:
        if not _coverage_data_files():
            failures.append(("coverage data collection", 1))
            print(
                "Coverage post-processing skipped: no coverage data files found.",
                file=sys.stderr,
            )
        else:
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
