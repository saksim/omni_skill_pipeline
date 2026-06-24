from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
SOURCE_TREE_FALLBACK_EXCLUDES = (
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "node_modules",
    "release-artifacts",
)
SOURCE_TREE_FALLBACK_SUFFIX_EXCLUDES = (
    ".egg-info",
)
SOURCE_TREE_FALLBACK_FILE_SUFFIX_EXCLUDES = (
    ".pyc",
)
SOURCE_TREE_FALLBACK_FILE_EXCLUDES = (
    ".DS_Store",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package release candidate artifacts for GitHub Actions and operator handoff.",
    )
    parser.add_argument(
        "--release-id",
        default=os.environ.get("RELEASE_ID", ""),
        help="Release id used in artifact names. Defaults to RELEASE_ID or short git sha.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Output directory. Defaults to release-artifacts/<release_id>.",
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory containing built Python distributions to copy into the release pack.",
    )
    parser.add_argument(
        "--coverage-xml",
        default="",
        help="Optional coverage.xml path to include. If supplied, the file must exist.",
    )
    parser.add_argument(
        "--source-ref",
        default="HEAD",
        help="Git ref archived into the source tarball. Defaults to HEAD.",
    )
    parser.add_argument(
        "--release-notes",
        default="",
        help=(
            "Optional Markdown notes file to include near the top of release-summary.md. "
            "Defaults to docs/releases/notes/<release_id>.md when present."
        ),
    )
    return parser.parse_args()


def _run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["GIT_CEILING_DIRECTORIES"] = os.pathsep.join(
        item
        for item in (str(REPO_ROOT.parent), env.get("GIT_CEILING_DIRECTORIES", ""))
        if item
    )
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        env=env,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _git_stdout(args: list[str], *, default: str = "") -> str:
    completed = _run_git(args, check=False)
    if completed.returncode != 0:
        return default
    return completed.stdout.strip()


def _project_metadata() -> dict[str, Any]:
    payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = payload.get("project", {})
    return {
        "name": project.get("name", "unknown"),
        "version": project.get("version", "0.0.0"),
        "requires_python": project.get("requires-python", ""),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_record(path: Path, *, role: str, output_dir: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(output_dir).as_posix(),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _validate_release_id(value: str) -> str:
    release_id = value.strip()
    if not release_id:
        short_sha = _git_stdout(["rev-parse", "--short=12", "HEAD"], default="unknown")
        release_id = "%s-%s" % (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), short_sha)
    if not RELEASE_ID_PATTERN.match(release_id):
        raise ValueError(
            "release_id may contain only letters, numbers, dot, underscore, and dash: %r" % release_id
        )
    return release_id


def _archive_source(source_ref: str, output_dir: Path, release_id: str) -> tuple[Path, dict[str, Any]]:
    archive_path = output_dir / ("omni-skill-pipeline-source-%s.tar.gz" % release_id)
    prefix = "omni-skill-pipeline-%s/" % release_id
    completed = _run_git(
        [
            "archive",
            "--format=tar.gz",
            "--prefix=%s" % prefix,
            "--output=%s" % archive_path,
            source_ref,
        ],
        check=False,
    )
    if completed.returncode != 0:
        return _archive_source_tree(
            archive_path=archive_path,
            output_dir=output_dir,
            prefix=prefix,
            git_error=completed.stderr.strip() or completed.stdout.strip(),
        )
    _assert_tar_readable(archive_path)
    return archive_path, {
        "source_archive_mode": "git_archive",
        "git_archive_error": "",
        "fallback_excludes": [],
    }


def _archive_source_tree(
    *,
    archive_path: Path,
    output_dir: Path,
    prefix: str,
    git_error: str,
) -> tuple[Path, dict[str, Any]]:
    excluded_roots = set(SOURCE_TREE_FALLBACK_EXCLUDES)
    resolved_output_dir = output_dir.resolve()
    resolved_archive_path = archive_path.resolve()
    with tarfile.open(archive_path, "w:gz") as archive:
        for path in sorted(REPO_ROOT.rglob("*")):
            resolved_path = path.resolve()
            if _is_source_tree_fallback_excluded(
                path,
                resolved_path=resolved_path,
                output_dir=resolved_output_dir,
                archive_path=resolved_archive_path,
                excluded_roots=excluded_roots,
            ):
                continue
            arcname = "%s%s" % (prefix, path.relative_to(REPO_ROOT).as_posix())
            archive.add(path, arcname=arcname, recursive=False)
    _assert_tar_readable(archive_path)
    return archive_path, {
        "source_archive_mode": "source_tree_fallback",
        "git_archive_error": git_error,
        "fallback_excludes": [
            *SOURCE_TREE_FALLBACK_EXCLUDES,
            *("*%s" % item for item in SOURCE_TREE_FALLBACK_SUFFIX_EXCLUDES),
            *("*%s" % item for item in SOURCE_TREE_FALLBACK_FILE_SUFFIX_EXCLUDES),
            *SOURCE_TREE_FALLBACK_FILE_EXCLUDES,
        ],
    }


def _is_source_tree_fallback_excluded(
    path: Path,
    *,
    resolved_path: Path,
    output_dir: Path,
    archive_path: Path,
    excluded_roots: set[str],
) -> bool:
    if resolved_path == archive_path:
        return True
    try:
        resolved_path.relative_to(output_dir)
        return True
    except ValueError:
        pass
    relative = path.relative_to(REPO_ROOT)
    parts = relative.parts
    if any(part in excluded_roots for part in parts):
        return True
    if any(part.endswith(SOURCE_TREE_FALLBACK_SUFFIX_EXCLUDES) for part in parts):
        return True
    if path.is_file() and path.name in SOURCE_TREE_FALLBACK_FILE_EXCLUDES:
        return True
    if path.is_file() and path.suffix in SOURCE_TREE_FALLBACK_FILE_SUFFIX_EXCLUDES:
        return True
    return False


def _assert_tar_readable(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        if not members:
            raise RuntimeError("source archive is empty: %s" % path)


def _is_distribution_file(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith((".whl", ".tar.gz", ".zip"))


def _copy_distributions(dist_dir: Path, output_dir: Path) -> list[Path]:
    if not dist_dir.exists():
        raise FileNotFoundError("distribution directory is missing: %s" % dist_dir)
    files = sorted(path for path in dist_dir.iterdir() if path.is_file() and _is_distribution_file(path))
    if not files:
        raise FileNotFoundError("distribution directory has no Python distributions: %s" % dist_dir)

    copied: list[Path] = []
    for path in files:
        target = output_dir / path.name
        shutil.copy2(path, target)
        copied.append(target)
    return copied


def _distribution_role(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".whl"):
        return "python_wheel"
    if name.endswith((".tar.gz", ".zip")):
        return "python_sdist"
    return "python_distribution"


def _copy_optional_coverage(coverage_xml: str, output_dir: Path) -> Path | None:
    if not coverage_xml:
        return None
    source = Path(coverage_xml)
    if not source.is_absolute():
        source = REPO_ROOT / source
    if not source.exists():
        raise FileNotFoundError("coverage XML is missing: %s" % source)
    target = output_dir / "coverage.xml"
    shutil.copy2(source, target)
    return target


def _read_release_notes(release_id: str, release_notes: str) -> str:
    if release_notes:
        path = Path(release_notes)
        if not path.is_absolute():
            path = REPO_ROOT / path
        if not path.exists():
            raise FileNotFoundError("release notes file is missing: %s" % path)
    else:
        path = REPO_ROOT / "docs" / "releases" / "notes" / ("%s.md" % release_id)
        if not path.exists():
            return ""

    return path.read_text(encoding="utf-8").strip()


def _write_manifest(
    output_dir: Path,
    *,
    release_id: str,
    source_ref: str,
    artifact_records: list[dict[str, Any]],
    source_archive_context: dict[str, Any],
) -> Path:
    metadata = _project_metadata()
    commit = _git_stdout(["rev-parse", source_ref], default="")
    status = _git_stdout(["status", "--short"], default="")
    source_archive_record = next(
        (item for item in artifact_records if item.get("role") == "source_archive"),
        {},
    )
    manifest = {
        "schema_version": "omni.release_artifacts.v1",
        "release_id": release_id,
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": metadata,
        "git": {
            "source_ref": source_ref,
            "commit": commit,
            "short_commit": commit[:12],
            "branch": _git_stdout(["rev-parse", "--abbrev-ref", "HEAD"], default=""),
            "dirty": bool(status),
        },
        "source_archive": {
            "source_archive_mode": str(source_archive_context.get("source_archive_mode", "")),
            "git_commit": commit or None,
            "git_dirty": bool(status),
            "source_archive_sha256": str(source_archive_record.get("sha256", "")),
            "fallback_excludes": list(source_archive_context.get("fallback_excludes", [])),
            "git_archive_error": str(source_archive_context.get("git_archive_error", "")),
        },
        "workflow": {
            "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "github_ref": os.environ.get("GITHUB_REF", ""),
            "github_ref_type": os.environ.get("GITHUB_REF_TYPE", ""),
            "github_ref_name": os.environ.get("GITHUB_REF_NAME", ""),
            "github_sha": os.environ.get("GITHUB_SHA", ""),
        },
        "artifact_contract": {
            "main_push": "release candidate artifact only",
            "tag_v_prefix": "GitHub Release publication",
            "manual_publish": "workflow_dispatch with publish_github_release=true and release_tag",
        },
        "artifacts": artifact_records,
    }
    path = output_dir / "release-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_summary(
    output_dir: Path,
    *,
    release_id: str,
    artifact_records: list[dict[str, Any]],
    release_notes: str,
) -> Path:
    metadata = _project_metadata()
    commit = _git_stdout(["rev-parse", "HEAD"], default="")
    lines = [
        "# Omni Skill Pipeline Release %s" % release_id,
        "",
    ]
    if release_notes:
        lines.extend(release_notes.splitlines())
        lines.append("")

    lines.extend(
        [
            "## Release Metadata",
            "",
            "- Project: `%s`" % metadata["name"],
            "- Version: `%s`" % metadata["version"],
            "- Commit: `%s`" % commit,
            "- Artifact count: `%s`" % len(artifact_records),
            "",
        ]
    )
    lines.extend(
        [
            "## Artifacts",
            "",
            "| File | Role | Bytes | SHA256 |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for record in artifact_records:
        lines.append(
            "| `%s` | `%s` | %s | `%s` |"
            % (record["path"], record["role"], record["bytes"], record["sha256"])
        )
    lines.extend(
        [
            "",
            "## Verification Boundary",
            "",
            "- CI and coverage gate must pass before this pack is generated.",
            "- This pack is a release candidate on `main` pushes.",
            "- A `v*` tag or manual `workflow_dispatch` with `publish_github_release=true` publishes a GitHub Release.",
            "- Full Docker/Postgres release switch remains available through `bash scripts/linux_release.sh`.",
            "",
        ]
    )
    path = output_dir / "release-summary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_sha256sums(output_dir: Path) -> Path:
    files = sorted(path for path in output_dir.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    path = output_dir / "SHA256SUMS"
    lines = ["%s  %s" % (_sha256(item), item.name) for item in files]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_release_pack(args: argparse.Namespace) -> Path:
    release_id = _validate_release_id(str(args.release_id or ""))
    release_notes = _read_release_notes(release_id, str(args.release_notes or ""))
    output_dir = Path(args.output_dir or (REPO_ROOT / "release-artifacts" / release_id))
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_records: list[dict[str, Any]] = []
    source_archive, source_archive_context = _archive_source(str(args.source_ref), output_dir, release_id)
    artifact_records.append(_artifact_record(source_archive, role="source_archive", output_dir=output_dir))

    dist_dir = Path(args.dist_dir)
    if not dist_dir.is_absolute():
        dist_dir = REPO_ROOT / dist_dir
    for distribution in _copy_distributions(dist_dir, output_dir):
        artifact_records.append(
            _artifact_record(distribution, role=_distribution_role(distribution), output_dir=output_dir)
        )

    coverage_path = _copy_optional_coverage(str(args.coverage_xml or ""), output_dir)
    if coverage_path is not None:
        artifact_records.append(_artifact_record(coverage_path, role="coverage_xml", output_dir=output_dir))

    _write_manifest(
        output_dir,
        release_id=release_id,
        source_ref=str(args.source_ref),
        artifact_records=artifact_records,
        source_archive_context=source_archive_context,
    )
    _write_summary(
        output_dir,
        release_id=release_id,
        artifact_records=artifact_records,
        release_notes=release_notes,
    )
    _write_sha256sums(output_dir)
    return output_dir


def main() -> int:
    args = _parse_args()
    try:
        output_dir = build_release_pack(args)
    except Exception as exc:
        print("release artifact packaging failed: %s" % exc, file=sys.stderr)
        return 1
    print("Release artifacts written: %s" % output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
