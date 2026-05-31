from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "gl27_handoff_escalations.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _handoff_report(
    *,
    handoff_status: str,
    ack_sla_status: str,
    breached_items: list[dict[str, Any]],
    overdue_items: list[dict[str, Any]],
    tracking_incomplete_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if tracking_incomplete_items is None:
        tracking_incomplete_items = []
    return {
        "schema_version": "real_trial_backfill_handoff.v1",
        "generated_at_utc": "2026-05-27T12:00:00Z",
        "handoff_status": handoff_status,
        "owner": "controlled-beta-ops",
        "acknowledgement_sla_snapshot": {
            "acknowledgement_sla_status": ack_sla_status,
            "pending_ack_within_sla_count": 0,
            "pending_ack_sla_breached_count": len(breached_items),
            "pending_ack_overdue_count": len(overdue_items),
            "pending_ack_missing_reference_timestamp_count": len(tracking_incomplete_items),
        },
        "pending_ack_queue_items": breached_items + overdue_items + tracking_incomplete_items,
        "pending_ack_sla_breached_queue_items": breached_items,
        "pending_ack_overdue_queue_items": overdue_items,
        "pending_ack_tracking_incomplete_queue_items": tracking_incomplete_items,
    }


def _queue_item(queue_item_id: str, *, action: str, modality: str = "text") -> dict[str, Any]:
    return {
        "queue_item_id": queue_item_id,
        "action_id": "gl23-slot-001-%s" % modality,
        "slot_index": 1,
        "required_modality": modality,
        "reason": "missing_target_launch_modality",
        "assignee": "controlled-beta-ops",
        "owner": "controlled-beta-ops",
        "pending_ack_age_hours": 26.5,
        "pending_ack_sla_deadline_utc": "2026-05-28T00:00:00Z",
        "pending_ack_overdue_deadline_utc": "2026-05-30T00:00:00Z",
        "escalation_action": action,
    }


class RealTrialBackfillHandoffEscalationsScriptTests(unittest.TestCase):
    def test_reports_overdue_escalation_and_fail_on_overdue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            handoff_report = root / "handoff-report.json"
            escalation_report = root / "escalation-report.json"

            _write_json(
                handoff_report,
                _handoff_report(
                    handoff_status="HANDOFF_OPERATOR_ACK_PENDING",
                    ack_sla_status="ACK_SLA_OVERDUE_ESCALATION",
                    breached_items=[],
                    overdue_items=[_queue_item("gl24-queue-gl23-slot-001-text", action="escalate_immediately")],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--handoff-report",
                    str(handoff_report),
                    "--output",
                    str(escalation_report),
                    "--summary-output",
                    "-",
                    "--fail-on-overdue",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("status=ESCALATION_OVERDUE_ACTION_REQUIRED", completed.stdout)

            payload = json.loads(escalation_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("escalation_status"), "ESCALATION_OVERDUE_ACTION_REQUIRED")
            counts = payload.get("escalation_counts", {})
            self.assertEqual(counts.get("overdue_item_count"), 1)
            self.assertEqual(counts.get("sla_breached_item_count"), 0)
            exports = payload.get("escalation_exports", {})
            overdue_items = exports.get("overdue_items", [])
            self.assertEqual(len(overdue_items), 1)
            self.assertEqual(overdue_items[0].get("queue_item_id"), "gl24-queue-gl23-slot-001-text")
            self.assertEqual(overdue_items[0].get("escalation_severity"), "overdue")

    def test_reports_breached_escalation_and_fail_on_breached(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            handoff_report = root / "handoff-report.json"
            escalation_report = root / "escalation-report.json"
            escalation_summary = root / "escalation-summary.md"

            _write_json(
                handoff_report,
                _handoff_report(
                    handoff_status="HANDOFF_OPERATOR_ACK_PENDING",
                    ack_sla_status="ACK_SLA_BREACH_PENDING_ACTION",
                    breached_items=[
                        _queue_item(
                            "gl24-queue-gl23-slot-002-audio",
                            action="notify_owner_and_track_until_acknowledged",
                            modality="audio",
                        )
                    ],
                    overdue_items=[],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--handoff-report",
                    str(handoff_report),
                    "--output",
                    str(escalation_report),
                    "--summary-output",
                    str(escalation_summary),
                    "--owner",
                    "beta-escalation-ops",
                    "--fail-on-breached",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("status=ESCALATION_BREACH_ACTION_REQUIRED", completed.stdout)

            payload = json.loads(escalation_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("owner"), "beta-escalation-ops")
            self.assertEqual(payload.get("escalation_status"), "ESCALATION_BREACH_ACTION_REQUIRED")
            counts = payload.get("escalation_counts", {})
            self.assertEqual(counts.get("sla_breached_item_count"), 1)
            self.assertEqual(counts.get("overdue_item_count"), 0)
            breached_items = payload.get("escalation_exports", {}).get("sla_breached_items", [])
            self.assertEqual(len(breached_items), 1)
            self.assertEqual(breached_items[0].get("escalation_severity"), "sla_breached")
            summary = escalation_summary.read_text(encoding="utf-8")
            self.assertIn("Escalation status: `ESCALATION_BREACH_ACTION_REQUIRED`", summary)

    def test_reports_not_required_when_no_escalations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            handoff_report = root / "handoff-report.json"
            escalation_report = root / "escalation-report.json"

            _write_json(
                handoff_report,
                _handoff_report(
                    handoff_status="HANDOFF_CLOSURE_ACKNOWLEDGED",
                    ack_sla_status="ACK_SLA_NOT_REQUIRED",
                    breached_items=[],
                    overdue_items=[],
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--handoff-report",
                    str(handoff_report),
                    "--output",
                    str(escalation_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(escalation_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("escalation_status"), "ESCALATION_NOT_REQUIRED")
            counts = payload.get("escalation_counts", {})
            self.assertEqual(counts.get("total_escalation_item_count"), 0)


if __name__ == "__main__":
    unittest.main()
