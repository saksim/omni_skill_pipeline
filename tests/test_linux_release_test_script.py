from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "linux_release.sh"
DOCKERFILE_PATH = REPO_ROOT / "Dockerfile"
ROOT_DOCKERIGNORE_PATH = REPO_ROOT / ".dockerignore"
TEST_DOCKERIGNORE_PATH = REPO_ROOT / "Dockerfile.test.dockerignore"


class LinuxReleaseTestScriptTests(unittest.TestCase):
    def test_script_has_source_preflight_for_runtime_contract_files(self) -> None:
        content = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("preflight_source_tree()", content)
        self.assertIn("preflight_release_environment()", content)
        self.assertIn("postgres_preflight()", content)
        self.assertIn("run_step source_preflight preflight_source_tree", content)
        self.assertIn("run_or_plan_step postgres_preflight postgres_preflight", content)
        self.assertIn("missing OMNI_TEST_POSTGRES_DSN", content)
        self.assertIn("docs/current/contracts/SKILL.template.md", content)
        self.assertIn("docs/current/contracts/skill.schema.json", content)
        self.assertIn("docs/current/contracts/skill-graph.schema.json", content)
        self.assertIn("src/omni_skill_pipeline/adapters/__init__.py", content)
        self.assertIn("src/omni_skill_pipeline/adapters/audio.py", content)
        self.assertIn("src/omni_skill_pipeline/adapters/image.py", content)
        self.assertIn("src/omni_skill_pipeline/adapters/tabular.py", content)
        self.assertIn("src/omni_skill_pipeline/adapters/text.py", content)
        self.assertIn("src/omni_skill_pipeline/adapters/video.py", content)
        self.assertIn("infra/sql/001_init.sql", content)
        self.assertIn("git check-ignore -v docs/current/contracts", content)

    def test_script_skips_runtime_dependent_stages_after_runtime_build_failure(self) -> None:
        content = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("runtime_image_ready()", content)
        self.assertIn("stage_succeeded build_runtime_image", content)
        self.assertIn('skip_step container_smoke "build_test_image or build_runtime_image did not pass"', content)
        self.assertIn('skip_step api_acceptance "build_test_image or build_runtime_image did not pass"', content)
        self.assertIn('skip_step linux_validation_suite "build_test_image or build_runtime_image did not pass"', content)
        self.assertIn('skip_step release_switch "build_test_image or build_runtime_image did not pass"', content)
        self.assertIn('skip_step ci_gate "build_test_image or postgres_preflight did not pass"', content)
        self.assertIn('skip_step build_runtime_image "source_preflight, docker_preflight, or postgres_preflight did not pass"', content)

    def test_script_dry_run_is_plan_only_except_source_preflight(self) -> None:
        content = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("--dry-run", content)
        self.assertIn("plan_step()", content)
        self.assertIn('overall="PLANNED"', content)
        self.assertIn("run_or_plan_step docker_preflight docker ps", content)
        self.assertIn("run_step source_preflight preflight_source_tree", content)
        self.assertIn("run_or_plan_step postgres_preflight postgres_preflight", content)

    def test_script_resets_generated_evidence_before_release_run(self) -> None:
        content = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("reset_generated_evidence()", content)
        self.assertIn("reset_generated_evidence\ncapture_meta", content)
        self.assertIn("e13-release-switch-decision-report.json", content)
        self.assertIn("e13-postgres-soak-benchmark-report.json", content)
        self.assertIn("e13-postgres-ga-benchmark-report.json", content)

    def test_release_validation_requires_postgres_evidence(self) -> None:
        content = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("--require-postgres", content)
        self.assertIn("postgres_dsn_configured=true", content)
        self.assertIn("postgres_dsn_configured=false", content)
        self.assertIn("postgres_connectivity_probe()", content)
        self.assertIn("ensure_release_postgres()", content)
        self.assertIn("pg_isready", content)
        self.assertIn("omni-release-postgres", content)
        self.assertIn("OMNI_RELEASE_MANAGE_POSTGRES", content)

    def test_docker_context_keeps_runtime_contracts_visible(self) -> None:
        root_ignore = ROOT_DOCKERIGNORE_PATH.read_text(encoding="utf-8")
        test_ignore = TEST_DOCKERIGNORE_PATH.read_text(encoding="utf-8")

        for content in (root_ignore, test_ignore):
            self.assertIn("!docs/current/contracts/", content)
            self.assertIn("!docs/current/contracts/**", content)
            self.assertIn("!infra/sql/001_init.sql", content)

    def test_runtime_dockerfile_copies_contract_files_explicitly(self) -> None:
        content = DOCKERFILE_PATH.read_text(encoding="utf-8")

        self.assertIn("COPY docs/current/contracts/SKILL.template.md", content)
        self.assertIn("docs/current/contracts/skill.schema.json", content)
        self.assertIn("docs/current/contracts/skill-graph.schema.json", content)
        self.assertIn("./docs/current/contracts/", content)


if __name__ == "__main__":
    unittest.main()
