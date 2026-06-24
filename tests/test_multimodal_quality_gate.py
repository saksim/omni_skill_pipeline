from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "multimodal_quality_gate.py"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _quality_record(
    *,
    loop_id: str,
    modality: str,
    scores: dict[str, int] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "loop_id": loop_id,
        "modality": modality,
        "quality_scores": scores
        or {
            "faithfulness": 4,
            "completeness": 4,
            "reusability": 4,
            "traceability": 4,
            "safety_redaction": 5,
            "agent_usability": 4,
        },
        "critical_issues": [],
        "minor_issues": [],
        "requires_human_review": True,
        "human_review_decision": "approved_for_beta_evidence",
    }
    if extra:
        payload.update(extra)
    return payload


class MultimodalQualityGateScriptTests(unittest.TestCase):
    def test_ready_when_all_required_modalities_have_passing_quality_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            evidence_path = root / "quality-evidence.json"
            report_path = root / "quality-report.json"
            _write_json(
                evidence_path,
                {
                    "quality_evidence": [
                        _quality_record(loop_id="RL-001", modality="text"),
                        _quality_record(
                            loop_id="RL-002",
                            modality="audio",
                            extra={"asr_status": "unavailable", "transcript_ref": "redacted-transcript.md"},
                        ),
                        _quality_record(
                            loop_id="RL-003",
                            modality="image",
                            extra={"ocr_confidence": 0.62, "uncertain_regions": ["header-total"]},
                        ),
                        _quality_record(
                            loop_id="RL-004",
                            modality="video",
                            extra={
                                "ocr_status": "unavailable",
                                "keyframe_status": "unavailable",
                                "graceful_degradation_note": "Transcript-first review was used.",
                            },
                        ),
                    ]
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--evidence",
                    str(evidence_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--fail-on-blocked",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("MULTIMODAL_QUALITY_GATE_READY", completed.stdout)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "MULTIMODAL_QUALITY_GATE_READY")
            self.assertEqual(payload.get("counts", {}).get("passed_record_count"), 4)
            self.assertEqual(payload.get("missing_required_modalities"), [])

    def test_blocked_when_score_or_review_contract_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            evidence_path = root / "quality-evidence.json"
            report_path = root / "quality-report.json"
            weak_scores = {
                "faithfulness": 3,
                "completeness": 4,
                "reusability": 4,
                "traceability": 4,
                "safety_redaction": 5,
                "agent_usability": 4,
            }
            _write_json(
                evidence_path,
                {
                    "quality_evidence": [
                        _quality_record(
                            loop_id="RL-003",
                            modality="image",
                            scores=weak_scores,
                            extra={
                                "critical_issues": ["Hallucinated source fact."],
                                "requires_human_review": False,
                                "human_review_decision": "pending",
                            },
                        )
                    ]
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--evidence",
                    str(evidence_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--required-modalities",
                    "image",
                    "--fail-on-blocked",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("status"), "MULTIMODAL_QUALITY_GATE_BLOCKED")
            codes = payload.get("records", [{}])[0].get("failure_codes", [])
            self.assertIn("quality_score_below_beta_threshold:faithfulness", codes)
            self.assertIn("critical_issues_present", codes)
            self.assertIn("requires_human_review_not_true", codes)
            self.assertIn("human_review_decision_not_approved", codes)

    def test_provider_fallback_contract_blocks_unsafe_degradation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            evidence_path = root / "quality-evidence.json"
            report_path = root / "quality-report.json"
            _write_json(
                evidence_path,
                {
                    "quality_evidence": [
                        _quality_record(
                            loop_id="RL-002",
                            modality="audio",
                            extra={"asr_status": "unavailable"},
                        ),
                        _quality_record(
                            loop_id="RL-003",
                            modality="image",
                            extra={"ocr_confidence": 0.2},
                        ),
                    ]
                },
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--evidence",
                    str(evidence_path),
                    "--output",
                    str(report_path),
                    "--summary-output",
                    "-",
                    "--required-modalities",
                    "audio,image",
                    "--fail-on-blocked",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            blocking_codes = payload.get("blocking_codes", [])
            self.assertIn("audio_asr_unavailable_without_transcript", blocking_codes)
            self.assertIn("ocr_low_confidence_without_uncertain_regions", blocking_codes)


if __name__ == "__main__":
    unittest.main()
