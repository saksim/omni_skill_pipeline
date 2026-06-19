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
    return parser.parse_args()


def _run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
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


def _archive_source(source_ref: str, output_dir: Path, release_id: str) -> Path:
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
        raise RuntimeError("git archive failed: %s" % (completed.stderr.strip() or completed.stdout.strip()))
    _assert_tar_readable(archive_path)
    return archive_path


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


def _write_manifest(
    output_dir: Path,
    *,
    release_id: str,
    source_ref: str,
    artifact_records: list[dict[str, Any]],
) -> Path:
    metadata = _project_metadata()
    commit = _git_stdout(["rev-parse", source_ref], default="")
    status = _git_stdout(["status", "--short"], default="")
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
) -> Path:
    metadata = _project_metadata()
    commit = _git_stdout(["rev-parse", "HEAD"], default="")
    lines = [
        "# Omni Skill Pipeline Release %s" % release_id,
        "",
        "- Project: `%s`" % metadata["name"],
        "- Version: `%s`" % metadata["version"],
        "- Commit: `%s`" % commit,
        "- Artifact count: `%s`" % len(artifact_records),
        "",
        "## Artifacts",
        "",
        "| File | Role | Bytes | SHA256 |",
        "| --- | --- | ---: | --- |",
    ]
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
    output_dir = Path(args.output_dir or (REPO_ROOT / "release-artifacts" / release_id))
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact_records: list[dict[str, Any]] = []
    source_archive = _archive_source(str(args.source_ref), output_dir, release_id)
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
    )
    _write_summary(output_dir, release_id=release_id, artifact_records=artifact_records)
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
