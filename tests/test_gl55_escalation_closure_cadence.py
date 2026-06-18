from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "scripts"
    / "gl55_escalation_closure_cadence.py"
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _gl54_report(
    *,
    status: str,
    generated_at_utc: str,
    rows: list[dict[str, Any]],
    warning_codes: list[str] | None = None,
    stale_open_item_count: int = 0,
    net_new_closed_item_count: int = 0,
    net_new_closed_backed_by_ack_ingestion_item_count_gl50: int = 0,
) -> dict[str, Any]:
    warnings = warning_codes if isinstance(warning_codes, list) else []
    open_count = sum(
        1 for row in rows if str(row.get("closure_item_status", "")).strip().lower() == "open"
    )
    return {
        "schema_version": "real_trial_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure.v1",
        "generated_at_utc": generated_at_utc,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status": status,
        "warning_codes": warnings,
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts": {
            "total_item_count": len(rows),
            "open_item_count": open_count,
            "previous_open_item_count": open_count,
            "carried_open_item_count": sum(
                1
                for row in rows
                if str(row.get("closure_progress_state", "")).strip().lower() == "carried_open"
            ),
            "stale_open_item_count": int(stale_open_item_count),
            "net_new_open_item_count": sum(
                1
                for row in rows
                if str(row.get("closure_progress_state", "")).strip().lower() == "net_new_open"
            ),
            "net_new_closed_item_count": int(net_new_closed_item_count),
            "net_new_closed_backed_by_ack_ingestion_item_count_gl50": int(
                net_new_closed_backed_by_ack_ingestion_item_count_gl50
            ),
            "net_new_closed_without_ack_ingestion_item_count_gl50": max(
                0,
                int(net_new_closed_item_count)
                - int(net_new_closed_backed_by_ack_ingestion_item_count_gl50),
            ),
            "ack_ingestion_closed_item_count_gl50": int(
                net_new_closed_backed_by_ack_ingestion_item_count_gl50
            ),
            "ack_ingestion_open_item_count_gl50": open_count,
        },
        "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows": rows,
    }


class RealTrialSubmissionQueueFollowupResolutionEscalationActionPlanClosureCadenceEscalationAcknowledgementClosureCadenceEscalationClosureCadenceScriptTests(
    unittest.TestCase
):
    def test_not_required_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl54 = root / "gl54.json"
            gl55 = root / "gl55.json"

            _write_json(
                gl54,
                _gl54_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_NOT_REQUIRED",
                    generated_at_utc="2026-05-31T00:00:00Z",
                    rows=[],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
                    str(gl54),
                    "--output",
                    str(gl55),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-05-31T01:00:00Z",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl55.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_NOT_REQUIRED",
            )
            cadence = payload.get("refresh_cadence", {})
            self.assertEqual(cadence.get("cadence_status"), "CADENCE_NOT_REQUIRED")
            self.assertEqual(cadence.get("next_refresh_due_utc"), "")
            self.assertEqual(payload.get("warning_codes"), [])

    def test_due_path_from_previous_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl54 = root / "gl54.json"
            gl55 = root / "gl55.json"

            _write_json(
                gl54,
                _gl54_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_PROGRESSING",
                    generated_at_utc="2026-05-31T00:00:00Z",
                    rows=[
                        {
                            "closure_item_id": "gl54-ack-closure-cadence-escalation-closure-gl53-esc-001",
                            "closure_item_status": "open",
                            "closure_progress_state": "net_new_open",
                            "required_modality_gl47": "text",
                            "action_id_gl48": "gl46-slot-001-text",
                        }
                    ],
                    net_new_closed_item_count=1,
                    net_new_closed_backed_by_ack_ingestion_item_count_gl50=1,
                ),
            )

            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
                    str(gl54),
                    "--output",
                    str(gl55),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-05-31T01:00:00Z",
                    "--refresh-interval-hours",
                    "24",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr + baseline.stdout)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
                    str(gl54),
                    "--output",
                    str(gl55),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-01T03:00:00Z",
                    "--refresh-interval-hours",
                    "24",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(gl55.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_DUE",
            )
            cadence = payload.get("refresh_cadence", {})
            self.assertEqual(cadence.get("cadence_status"), "CADENCE_DUE")
            warning_codes = payload.get("warning_codes", [])
            self.assertIn(
                "acknowledgement_closure_cadence_escalation_closure_cadence_due",
                warning_codes,
            )
            rows = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_rows",
                [],
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].get("cadence_item_status"), "refresh_due")

    def test_overdue_stalled_fail_on_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gl54 = root / "gl54.json"
            gl55 = root / "gl55.json"

            _write_json(
                gl54,
                _gl54_report(
                    status="ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_STALLED",
                    generated_at_utc="2026-05-31T00:00:00Z",
                    rows=[
                        {
                            "closure_item_id": "gl54-ack-closure-cadence-escalation-closure-gl53-esc-001",
                            "closure_item_status": "open",
                            "closure_progress_state": "carried_open",
                            "required_modality_gl47": "text",
                            "action_id_gl48": "gl46-slot-001-text",
                        }
                    ],
                    stale_open_item_count=1,
                ),
            )

            baseline = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
                    str(gl54),
                    "--output",
                    str(gl55),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-05-31T01:00:00Z",
                    "--refresh-interval-hours",
                    "24",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr + baseline.stdout)

            second = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
                    str(gl54),
                    "--output",
                    str(gl55),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-01T03:30:00Z",
                    "--refresh-interval-hours",
                    "24",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
                    str(gl54),
                    "--output",
                    str(gl55),
                    "--summary-output",
                    "-",
                    "--now-utc",
                    "2026-06-02T05:00:00Z",
                    "--refresh-interval-hours",
                    "24",
                    "--overdue-stalled-cycles",
                    "2",
                    "--fail-on-overdue-stalled",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            payload = json.loads(gl55.read_text(encoding="utf-8"))
            self.assertEqual(
                payload.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status"
                ),
                "ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACK_INGESTION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_OVERDUE_STALLED",
            )
            counts = payload.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts",
                {},
            )
            self.assertGreaterEqual(int(counts.get("stall_cycle_count", 0)), 2)
            warning_codes = payload.get("warning_codes", [])
            self.assertIn(
                "acknowledgement_closure_cadence_escalation_closure_cadence_overdue_stalled",
                warning_codes,
            )
            self.assertIn("acknowledgement_closure_cadence_escalation_closure_stalled", warning_codes)


if __name__ == "__main__":
    unittest.main()
