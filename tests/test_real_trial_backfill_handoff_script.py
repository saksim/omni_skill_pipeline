from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_real_trial_backfill_handoff.py"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _intake_actions_report(*, actions: list[dict[str, Any]], status: str = "ACTIONS_PENDING") -> dict[str, Any]:
    pending_actions = []
    for item in actions:
        action_status = str(item.get("action_status", "pending")).strip().lower()
        if action_status != "closed":
            pending_actions.append(
                {
                    "action_id": item.get("action_id"),
                    "slot_index": item.get("slot_index"),
                    "required_modality": item.get("required_modality"),
                    "reason": item.get("reason"),
                    "owner": item.get("owner", "controlled-beta-ops"),
                }
            )
    return {
        "schema_version": "real_trial_backfill_intake_actions.v1",
        "generated_at_utc": "2026-05-27T00:00:00Z",
        "intake_status": status,
        "launch_gap_snapshot": {
            "program_status": "COLLECTION_INCOMPLETE",
            "missing_complete_loops_to_threshold": max(0, len(pending_actions)),
            "missing_modalities_to_threshold": 1 if pending_actions else 0,
            "blockers": ["real_loop_volume_below_threshold"] if pending_actions else [],
        },
        "actions": actions,
        "pending_actions": pending_actions,
    }


def _action(slot_index: int, modality: str, *, status: str = "pending") -> dict[str, Any]:
    return {
        "action_id": "gl23-slot-%03d-%s" % (slot_index, modality),
        "slot_index": slot_index,
        "required_modality": modality,
        "reason": "missing_target_launch_modality",
        "action_status": status,
        "execution_status": "fulfilled" if status == "closed" else "pending",
        "owner": "controlled-beta-ops",
        "title": "Collect real %s loop" % modality,
        "operator_task": "Collect real %s loop and attach review trace." % modality,
        "closure_evidence_requirements": {
            "required_loop_manifest_fields": [
                "loop_id",
                "modality",
                "evidence_origin",
                "launch_gate_eligible",
                "source_system",
                "source_reference",
                "collected_at_utc",
                "review_task_id",
                "reviewed_by",
                "reviewed_at_utc",
            ],
            "required_field_values": {
                "evidence_origin": "real",
                "launch_gate_eligible": True,
                "status": "complete",
                "modality": modality,
            },
        },
    }


def _collection_report(*, loops: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_loop_collection.v1",
        "generated_at_utc": "2026-05-27T00:05:00Z",
        "collected_real_launch_gate_eligible_loops": loops,
    }


def _acknowledgements_report(*, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "real_trial_backfill_handoff_acknowledgements.v1",
        "generated_at_utc": "2026-05-27T00:15:00Z",
        "acknowledgements": rows,
    }


def _loop(
    loop_id: str,
    modality: str,
    reviewed_at: str,
    *,
    backfill_slot_index: int | None = None,
    backfill_action_id: str = "",
) -> dict[str, Any]:
    row = {
        "loop_id": loop_id,
        "modality": modality,
        "source_system": "pilot-ops",
        "source_reference": "ticket://%s" % loop_id,
        "collected_at_utc": reviewed_at,
        "review_task_id": "review-%s" % loop_id,
        "reviewed_by": "reviewer-a",
        "reviewed_at_utc": reviewed_at,
        "source_report_path": "memory://collection",
    }
    if backfill_slot_index is not None:
        row["backfill_slot_index"] = int(backfill_slot_index)
    if backfill_action_id:
        row["backfill_action_id"] = str(backfill_action_id)
    return row


class RealTrialBackfillHandoffScriptTests(unittest.TestCase):
    def test_handoff_pending_when_no_matching_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions.json"
            collection_report = root / "collection-report.json"
            handoff_report = root / "handoff-report.json"
            handoff_summary = root / "handoff-summary.md"

            _write_json(
                intake_report,
                _intake_actions_report(actions=[_action(1, "video", status="pending")]),
            )
            _write_json(collection_report, _collection_report(loops=[]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(handoff_report),
                    "--summary-output",
                    str(handoff_summary),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("status=HANDOFF_ACTIONS_PENDING", completed.stdout)

            payload = json.loads(handoff_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("handoff_status"), "HANDOFF_ACTIONS_PENDING")
            counts = payload.get("queue_item_counts", {})
            self.assertEqual(counts.get("total_queue_item_count"), 1)
            self.assertEqual(counts.get("open_queue_item_count"), 1)
            self.assertEqual(counts.get("closure_acknowledged_count"), 0)
            queue_items = payload.get("queue_items", [])
            self.assertEqual(queue_items[0].get("queue_status"), "open")
            self.assertEqual(queue_items[0].get("closure_acknowledgement", {}).get("status"), "pending_submission")
            summary = handoff_summary.read_text(encoding="utf-8")
            self.assertIn("Open queue items: `1`", summary)

    def test_handoff_acknowledges_closure_from_real_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions.json"
            collection_report = root / "collection-report.json"
            acknowledgements_report = root / "acknowledgements-report.json"
            handoff_report = root / "handoff-report.json"

            _write_json(
                intake_report,
                _intake_actions_report(actions=[_action(1, "text", status="pending")]),
            )
            _write_json(
                collection_report,
                _collection_report(
                    loops=[
                        _loop("real-text-001", "text", "2026-05-27T00:10:00Z"),
                    ]
                ),
            )
            _write_json(
                acknowledgements_report,
                _acknowledgements_report(
                    rows=[
                        {
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "action_id": "gl23-slot-001-text",
                            "submitted_loop_id": "real-text-001",
                            "submitted_modality": "text",
                            "acknowledged_by": "ops-reviewer-1",
                            "acknowledged_at_utc": "2026-05-27T00:20:00Z",
                            "notes": "linkage confirmed",
                        }
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--collection-report",
                    str(collection_report),
                    "--acknowledgements-report",
                    str(acknowledgements_report),
                    "--output",
                    str(handoff_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("status=HANDOFF_CLOSURE_ACKNOWLEDGED", completed.stdout)

            payload = json.loads(handoff_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("handoff_status"), "HANDOFF_CLOSURE_ACKNOWLEDGED")
            counts = payload.get("queue_item_counts", {})
            self.assertEqual(counts.get("total_queue_item_count"), 1)
            self.assertEqual(counts.get("open_queue_item_count"), 0)
            self.assertEqual(counts.get("closure_acknowledged_count"), 1)
            queue_items = payload.get("queue_items", [])
            self.assertEqual(queue_items[0].get("queue_status"), "closure_acknowledged")
            ack = queue_items[0].get("closure_acknowledgement", {})
            self.assertEqual(ack.get("status"), "acknowledged")
            self.assertEqual(ack.get("linked_submission", {}).get("loop_id"), "real-text-001")
            self.assertEqual(ack.get("linked_submission", {}).get("submission_linkage_strategy"), "modality_fallback")

    def test_handoff_submission_linked_requires_operator_acknowledgement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions.json"
            collection_report = root / "collection-report.json"
            handoff_report = root / "handoff-report.json"

            _write_json(
                intake_report,
                _intake_actions_report(actions=[_action(1, "text", status="pending")]),
            )
            _write_json(
                collection_report,
                _collection_report(
                    loops=[
                        _loop("real-text-001", "text", "2026-05-27T00:10:00Z"),
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(handoff_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("status=HANDOFF_OPERATOR_ACK_PENDING", completed.stdout)

            payload = json.loads(handoff_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("handoff_status"), "HANDOFF_OPERATOR_ACK_PENDING")
            counts = payload.get("queue_item_counts", {})
            self.assertEqual(counts.get("open_queue_item_count"), 0)
            self.assertEqual(counts.get("submission_linked_pending_ack_count"), 1)
            self.assertEqual(counts.get("closure_acknowledged_count"), 0)
            queue_items = payload.get("queue_items", [])
            self.assertEqual(queue_items[0].get("queue_status"), "submission_linked_pending_ack")
            self.assertEqual(
                queue_items[0].get("closure_acknowledgement", {}).get("status"),
                "pending_operator_acknowledgement",
            )

    def test_handoff_acknowledges_closure_when_submission_and_ack_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions.json"
            collection_report = root / "collection-report.json"
            acknowledgements_report = root / "acknowledgements-report.json"
            handoff_report = root / "handoff-report.json"

            _write_json(
                intake_report,
                _intake_actions_report(actions=[_action(1, "text", status="pending")]),
            )
            _write_json(
                collection_report,
                _collection_report(
                    loops=[
                        _loop("real-text-001", "text", "2026-05-27T00:10:00Z"),
                    ]
                ),
            )
            _write_json(
                acknowledgements_report,
                _acknowledgements_report(
                    rows=[
                        {
                            "queue_item_id": "gl24-queue-gl23-slot-001-text",
                            "action_id": "gl23-slot-001-text",
                            "submitted_loop_id": "real-text-001",
                            "submitted_modality": "text",
                            "acknowledged_by": "ops-reviewer-1",
                            "acknowledged_at_utc": "2026-05-27T00:20:00Z",
                            "notes": "linkage confirmed",
                        }
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--collection-report",
                    str(collection_report),
                    "--acknowledgements-report",
                    str(acknowledgements_report),
                    "--output",
                    str(handoff_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("status=HANDOFF_CLOSURE_ACKNOWLEDGED", completed.stdout)

            payload = json.loads(handoff_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("handoff_status"), "HANDOFF_CLOSURE_ACKNOWLEDGED")
            counts = payload.get("queue_item_counts", {})
            self.assertEqual(counts.get("submission_linked_pending_ack_count"), 0)
            self.assertEqual(counts.get("closure_acknowledged_count"), 1)
            queue_items = payload.get("queue_items", [])
            self.assertEqual(queue_items[0].get("queue_status"), "closure_acknowledged")
            ack = queue_items[0].get("closure_acknowledgement", {})
            self.assertEqual(ack.get("status"), "acknowledged")
            self.assertEqual(ack.get("linked_submission", {}).get("loop_id"), "real-text-001")
            self.assertEqual(ack.get("operator_acknowledgement", {}).get("submitted_loop_id"), "real-text-001")
            self.assertEqual(ack.get("linked_submission", {}).get("submission_linkage_strategy"), "modality_fallback")

    def test_handoff_prefers_action_and_slot_linkage_over_modality_pool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions.json"
            collection_report = root / "collection-report.json"
            handoff_report = root / "handoff-report.json"

            _write_json(
                intake_report,
                _intake_actions_report(actions=[_action(1, "text", status="pending")]),
            )
            _write_json(
                collection_report,
                _collection_report(
                    loops=[
                        _loop(
                            "real-text-generic",
                            "text",
                            "2026-05-27T00:01:00Z",
                        ),
                        _loop(
                            "real-text-linked",
                            "text",
                            "2026-05-27T00:02:00Z",
                            backfill_slot_index=1,
                            backfill_action_id="gl23-slot-001-text",
                        ),
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(handoff_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

            payload = json.loads(handoff_report.read_text(encoding="utf-8"))
            queue_items = payload.get("queue_items", [])
            self.assertEqual(len(queue_items), 1)
            queue_item = queue_items[0]
            self.assertEqual(queue_item.get("submission_linkage_strategy"), "action_id_and_slot_index")
            linked_submission = queue_item.get("closure_acknowledgement", {}).get("linked_submission", {})
            self.assertEqual(linked_submission.get("loop_id"), "real-text-linked")
            self.assertEqual(linked_submission.get("submission_linkage_strategy"), "action_id_and_slot_index")

            linkage_snapshot = payload.get("submission_linkage_snapshot", {})
            self.assertEqual(linkage_snapshot.get("linkage_strategy_counts", {}).get("action_id_and_slot_index"), 1)
            self.assertEqual(linkage_snapshot.get("unlinked_submission_count"), 1)
            unlinked = linkage_snapshot.get("unlinked_submissions", [])
            self.assertEqual(len(unlinked), 1)
            self.assertEqual(unlinked[0].get("loop_id"), "real-text-generic")

    def test_handoff_reports_slot_only_linkage_when_action_id_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions.json"
            collection_report = root / "collection-report.json"
            handoff_report = root / "handoff-report.json"

            _write_json(
                intake_report,
                _intake_actions_report(actions=[_action(2, "audio", status="pending")]),
            )
            _write_json(
                collection_report,
                _collection_report(
                    loops=[
                        _loop(
                            "real-audio-slot-only",
                            "audio",
                            "2026-05-27T00:03:00Z",
                            backfill_slot_index=2,
                        ),
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(handoff_report),
                    "--summary-output",
                    "-",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            payload = json.loads(handoff_report.read_text(encoding="utf-8"))
            queue_items = payload.get("queue_items", [])
            self.assertEqual(queue_items[0].get("submission_linkage_strategy"), "slot_index_only")
            linked_submission = queue_items[0].get("closure_acknowledgement", {}).get("linked_submission", {})
            self.assertEqual(linked_submission.get("loop_id"), "real-audio-slot-only")

    def test_fail_on_open_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions.json"
            collection_report = root / "collection-report.json"

            _write_json(
                intake_report,
                _intake_actions_report(actions=[_action(1, "audio", status="pending")]),
            )
            _write_json(collection_report, _collection_report(loops=[]))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    "-",
                    "--summary-output",
                    "-",
                    "--fail-on-open",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("status=HANDOFF_ACTIONS_PENDING", completed.stdout)

    def test_handoff_ack_sla_overdue_and_fail_on_ack_overdue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions.json"
            collection_report = root / "collection-report.json"
            handoff_report = root / "handoff-report.json"

            _write_json(
                intake_report,
                _intake_actions_report(actions=[_action(1, "text", status="pending")]),
            )
            _write_json(
                collection_report,
                _collection_report(
                    loops=[
                        _loop("real-text-001", "text", "2026-05-27T00:00:00Z"),
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(handoff_report),
                    "--summary-output",
                    "-",
                    "--pending-ack-sla-hours",
                    "24",
                    "--pending-ack-overdue-hours",
                    "72",
                    "--now-utc",
                    "2026-05-31T12:00:00Z",
                    "--fail-on-ack-overdue",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr + completed.stdout)
            self.assertIn("ack_sla_status=ACK_SLA_OVERDUE_ESCALATION", completed.stdout)

            payload = json.loads(handoff_report.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("handoff_status"), "HANDOFF_OPERATOR_ACK_PENDING")
            sla = payload.get("acknowledgement_sla_snapshot", {})
            self.assertEqual(sla.get("acknowledgement_sla_status"), "ACK_SLA_OVERDUE_ESCALATION")
            self.assertEqual(sla.get("pending_ack_overdue_count"), 1)
            self.assertEqual(sla.get("pending_ack_sla_breached_count"), 0)
            self.assertEqual(sla.get("pending_ack_within_sla_count"), 0)
            overdue_items = sla.get("pending_ack_overdue_queue_items", [])
            self.assertEqual(len(overdue_items), 1)
            self.assertEqual(overdue_items[0].get("queue_item_id"), "gl24-queue-gl23-slot-001-text")
            self.assertEqual(overdue_items[0].get("escalation_action"), "escalate_immediately")

            queue_items = payload.get("queue_items", [])
            self.assertEqual(queue_items[0].get("queue_status"), "submission_linked_pending_ack")
            pending_ack = queue_items[0].get("closure_acknowledgement", {})
            self.assertEqual(pending_ack.get("pending_ack_sla_state"), "overdue")
            self.assertEqual(pending_ack.get("escalation_action"), "escalate_immediately")

    def test_handoff_ack_sla_breached_without_overdue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            intake_report = root / "intake-actions.json"
            collection_report = root / "collection-report.json"
            handoff_report = root / "handoff-report.json"

            _write_json(
                intake_report,
                _intake_actions_report(actions=[_action(1, "text", status="pending")]),
            )
            _write_json(
                collection_report,
                _collection_report(
                    loops=[
                        _loop("real-text-001", "text", "2026-05-27T00:00:00Z"),
                    ]
                ),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--intake-actions-report",
                    str(intake_report),
                    "--collection-report",
                    str(collection_report),
                    "--output",
                    str(handoff_report),
                    "--summary-output",
                    "-",
                    "--pending-ack-sla-hours",
                    "24",
                    "--pending-ack-overdue-hours",
                    "72",
                    "--now-utc",
                    "2026-05-28T12:30:00Z",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn("ack_sla_status=ACK_SLA_BREACH_PENDING_ACTION", completed.stdout)

            payload = json.loads(handoff_report.read_text(encoding="utf-8"))
            sla = payload.get("acknowledgement_sla_snapshot", {})
            self.assertEqual(sla.get("acknowledgement_sla_status"), "ACK_SLA_BREACH_PENDING_ACTION")
            self.assertEqual(sla.get("pending_ack_overdue_count"), 0)
            self.assertEqual(sla.get("pending_ack_sla_breached_count"), 1)
            breached_items = sla.get("pending_ack_sla_breached_queue_items", [])
            self.assertEqual(len(breached_items), 1)
            self.assertEqual(
                breached_items[0].get("escalation_action"),
                "notify_owner_and_track_until_acknowledged",
            )


if __name__ == "__main__":
    unittest.main()
