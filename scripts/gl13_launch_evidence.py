from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_LOOP_COLLECTION_SCRIPT = REPO_ROOT / "scripts" / "gl12_collect_loops.py"
REAL_LOOP_BACKFILL_EXECUTION_SCRIPT = REPO_ROOT / "scripts" / "gl22_backfill_exec.py"
REAL_LOOP_BACKFILL_INTAKE_ACTIONS_SCRIPT = REPO_ROOT / "scripts" / "gl23_intake_actions.py"
REAL_LOOP_BACKFILL_SUBMISSION_TEMPLATES_SCRIPT = (
    REPO_ROOT / "scripts" / "gl31_submission_templates.py"
)
REAL_LOOP_BACKFILL_SUBMISSION_CONSUMPTION_SCRIPT = (
    REPO_ROOT / "scripts" / "gl33_submission_consumption.py"
)
REAL_LOOP_SUBMISSION_THROUGHPUT_SCRIPT = (
    REPO_ROOT / "scripts" / "gl35_submission_throughput.py"
)
REAL_LOOP_SUBMISSION_QUEUE_SCRIPT = (
    REPO_ROOT / "scripts" / "gl37_submission_queue.py"
)
REAL_LOOP_SUBMISSION_QUEUE_COMPLETION_SCRIPT = (
    REPO_ROOT / "scripts" / "gl38_queue_completion.py"
)
REAL_LOOP_SUBMISSION_QUEUE_COMMITMENTS_SCRIPT = (
    REPO_ROOT / "scripts" / "gl39_queue_commitments.py"
)
REAL_LOOP_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_SCRIPT = (
    REPO_ROOT / "scripts" / "gl40_commitment_closure.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_SCRIPT = (
    REPO_ROOT / "scripts" / "gl41_queue_followup.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_SCRIPT = (
    REPO_ROOT / "scripts" / "gl42_followup_resolution.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_SCRIPT = (
    REPO_ROOT / "scripts" / "gl43_resolution_escalations.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACKNOWLEDGEMENTS_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl44_escalation_ack.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_THROUGHPUT_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl45_escalation_throughput.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl46_action_plan.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl47_action_plan_closure.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl48_action_plan_cadence.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATIONS_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl49_cadence_escalations.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_INGESTION_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl50_ack_ingestion.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl51_ack_closure.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl52_ack_closure_cadence.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATIONS_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl53_ack_cadence_escalations.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl54_ack_escalation_closure.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl55_escalation_closure_cadence.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl56_closure_cadence_escalations.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl57_closure_cadence_escalation_closure.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl58_closure_cadence_escalation_closure_cadence.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl59_closure_cadence_escalation_closure_cadence_escalations.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl60_closure_cadence_escalation_closure_cadence_escalation_closure.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl61_closure_cadence_escalation_closure_cadence_escalation_closure_cadence.py"
)
REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "gl62_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations.py"
)
REAL_LOOP_BACKFILL_HANDOFF_SCRIPT = REPO_ROOT / "scripts" / "gl24_handoff.py"
REAL_LOOP_BACKFILL_HANDOFF_ESCALATIONS_SCRIPT = (
    REPO_ROOT / "scripts" / "gl27_handoff_escalations.py"
)
TRIAL_METRICS_COLLECTOR_SCRIPT = REPO_ROOT / "scripts" / "trial_metrics.py"
LAUNCH_READINESS_GATE_SCRIPT = REPO_ROOT / "scripts" / "launch_gate.py"

DEFAULT_RUN_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "controlled-trial-run-report.json"
)
DEFAULT_COLLECTION_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-report.json"
)
DEFAULT_COLLECTION_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-collection-summary.md"
)
DEFAULT_REAL_TRIAL_MANIFEST = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-metrics-manifest.json"
)
DEFAULT_BACKFILL_PLAN_OUTPUT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-backfill-plan.json"
)
DEFAULT_BACKFILL_EXECUTION_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-execution-report.json"
)
DEFAULT_BACKFILL_EXECUTION_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-execution-summary.md"
)
DEFAULT_BACKFILL_INTAKE_ACTIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-intake-actions-report.json"
)
DEFAULT_BACKFILL_INTAKE_ACTIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-intake-actions-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_TEMPLATES_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-templates-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_TEMPLATES_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-templates-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_MANIFEST_TEMPLATE = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-manifest.template.json"
)
DEFAULT_BACKFILL_SUBMISSION_REAL_INPUTS = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-real-inputs.json"
)
DEFAULT_BACKFILL_SUBMISSION_CONSUMPTION_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-consumption-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_CONSUMPTION_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-consumption-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_CONSUMED_MANIFEST = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "manifests"
    / "real-trial-backfill-submission-manifest.consumed.json"
)
DEFAULT_BACKFILL_SUBMISSION_THROUGHPUT_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-throughput-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_THROUGHPUT_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-throughput-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMPLETION_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-completion-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMPLETION_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-completion-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENTS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitments-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENTS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitments-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitment-closure-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-commitment-closure-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalations-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalations-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACKNOWLEDGEMENTS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-acknowledgements-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACKNOWLEDGEMENTS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-acknowledgements-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_THROUGHPUT_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-throughput-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_THROUGHPUT_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-throughput-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_INGESTION_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_INGESTION_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-summary.md"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-report.json"
)
DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-summary.md"
)
DEFAULT_BACKFILL_HANDOFF_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-report.json"
)
DEFAULT_BACKFILL_HANDOFF_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-summary.md"
)
DEFAULT_BACKFILL_HANDOFF_ESCALATIONS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-escalations-report.json"
)
DEFAULT_BACKFILL_HANDOFF_ESCALATIONS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-backfill-handoff-escalations-summary.md"
)
DEFAULT_TRIAL_METRICS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "trial-metrics-report.json"
)
DEFAULT_TRIAL_METRICS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "trial-metrics-summary.md"
)
DEFAULT_LAUNCH_READINESS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "broad-launch-readiness-report.json"
)
DEFAULT_LAUNCH_READINESS_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "broad-launch-readiness-summary.md"
)
DEFAULT_RELEASE_SWITCH_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "e13-release-switch-decision-report.json"
)
DEFAULT_CURRENT_STATUS_DOC = REPO_ROOT / "docs" / "working" / "status" / "CURRENT_STATUS.md"
DEFAULT_AGENT_SMOKE_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "controlled-trial"
    / "agent-smoke-report.json"
)
DEFAULT_DOC_SYNC_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "e13-doc-sync-check-report.json"
)
DEFAULT_OPERATIONS_READINESS_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "operations-readiness-report.json"
)
DEFAULT_EVIDENCE_PACK = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-launch-evidence-pack.json"
)
DEFAULT_MANIFEST_PREFLIGHT_REPORT = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-manifest-preflight-report.json"
)
DEFAULT_MANIFEST_PREFLIGHT_SUMMARY = (
    REPO_ROOT
    / "docs"
    / "working"
    / "status"
    / "baselines"
    / "real-trial-loop-collection"
    / "real-trial-loop-manifest-preflight-summary.md"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the real-trial launch evidence pipeline: "
            "GL-12 loop collection -> trial metrics report -> broad launch readiness gate."
        )
    )
    parser.add_argument(
        "--run-report",
        action="append",
        default=[],
        help="Path to controlled-trial run report JSON. Repeat for multiple inputs.",
    )
    parser.add_argument(
        "--loop-manifest",
        action="append",
        default=[],
        help=(
            "Path to loop manifest JSON with top-level loops list. Repeat for multiple inputs. "
            "Use this for real controlled external Beta loop evidence."
        ),
    )
    parser.add_argument(
        "--loop-manifest-dir",
        action="append",
        default=[],
        help=(
            "Directory containing loop manifest JSON files. Repeat for multiple directories. "
            "Use with --loop-manifest-pattern for batch ingestion."
        ),
    )
    parser.add_argument(
        "--loop-manifest-pattern",
        default="*.json",
        help="Glob pattern used when expanding --loop-manifest-dir (default: *.json).",
    )
    parser.add_argument(
        "--loop-manifest-recursive",
        action="store_true",
        help="Recursively scan --loop-manifest-dir when collecting loop manifests.",
    )
    parser.add_argument(
        "--strict-loop-manifest-contract",
        action="store_true",
        help=(
            "Fail when any loop-manifest JSON discovered by explicit path or directory input "
            "does not provide top-level loops list."
        ),
    )
    parser.add_argument("--collection-report-output", default=str(DEFAULT_COLLECTION_REPORT))
    parser.add_argument("--collection-summary-output", default=str(DEFAULT_COLLECTION_SUMMARY))
    parser.add_argument("--real-trial-manifest-output", default=str(DEFAULT_REAL_TRIAL_MANIFEST))
    parser.add_argument("--backfill-plan-output", default=str(DEFAULT_BACKFILL_PLAN_OUTPUT))
    parser.add_argument("--backfill-execution-output", default=str(DEFAULT_BACKFILL_EXECUTION_REPORT))
    parser.add_argument("--backfill-execution-summary-output", default=str(DEFAULT_BACKFILL_EXECUTION_SUMMARY))
    parser.add_argument("--backfill-intake-actions-output", default=str(DEFAULT_BACKFILL_INTAKE_ACTIONS_REPORT))
    parser.add_argument("--backfill-intake-actions-summary-output", default=str(DEFAULT_BACKFILL_INTAKE_ACTIONS_SUMMARY))
    parser.add_argument("--backfill-intake-owner", default="controlled-beta-ops")
    parser.add_argument("--backfill-submission-templates-output", default=str(DEFAULT_BACKFILL_SUBMISSION_TEMPLATES_REPORT))
    parser.add_argument(
        "--backfill-submission-templates-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_TEMPLATES_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-manifest-template-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_MANIFEST_TEMPLATE),
    )
    parser.add_argument(
        "--backfill-submission-real-inputs",
        default=str(DEFAULT_BACKFILL_SUBMISSION_REAL_INPUTS),
    )
    parser.add_argument(
        "--backfill-submission-consumption-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_CONSUMPTION_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-consumption-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_CONSUMPTION_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-consumed-manifest-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_CONSUMED_MANIFEST),
    )
    parser.add_argument(
        "--backfill-submission-throughput-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_THROUGHPUT_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-throughput-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_THROUGHPUT_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-completion-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMPLETION_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-completion-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMPLETION_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-commitments-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENTS_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-commitments-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENTS_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-commitment-closure-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-commitment-closure-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalations-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalations-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-acknowledgements-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACKNOWLEDGEMENTS_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-acknowledgements-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACKNOWLEDGEMENTS_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-throughput-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_THROUGHPUT_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-throughput-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_THROUGHPUT_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-summary-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_SUMMARY),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-output",
        default=str(DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_REPORT),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATIONS_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATIONS_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_INGESTION_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_INGESTION_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATIONS_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATIONS_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_REPORT
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-summary-output",
        default=str(
            DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SUMMARY
        ),
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-59 escalation evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalate-after-due-hours",
        type=float,
        default=24.0,
        help="GL-59 escalation threshold hours after GL-58 cadence due timestamp (default: 24).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-refresh-interval-hours",
        type=float,
        default=24.0,
        help="GL-55 escalation-closure cadence refresh interval (hours).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-overdue-stalled-cycles",
        type=int,
        default=2,
        help="GL-55 overdue stalled cycle threshold (default: 2).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-55 escalation-closure cadence evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-56 escalation-closure-cadence escalation evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalate-after-due-hours",
        type=float,
        default=24.0,
        help="GL-56 escalation threshold hours after GL-55 cadence due timestamp (default: 24).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-53 acknowledgement-closure cadence escalation evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-refresh-interval-hours",
        type=float,
        default=24.0,
        help="GL-58 escalation-closure cadence refresh interval (hours).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-overdue-stalled-cycles",
        type=int,
        default=2,
        help="GL-58 overdue stalled cycle threshold (default: 2).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-58 escalation-closure cadence evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-refresh-interval-hours",
        type=float,
        default=24.0,
        help="GL-61 escalation-closure-cadence refresh interval (hours).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-overdue-stalled-cycles",
        type=int,
        default=2,
        help="GL-61 overdue stalled cycle threshold (default: 2).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-61 escalation-closure-cadence evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-62 escalation evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalate-after-due-hours",
        type=float,
        default=24.0,
        help="GL-62 escalation threshold hours after GL-61 cadence due timestamp (default: 24).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalate-after-due-hours",
        type=float,
        default=24.0,
        help="GL-53 escalation threshold hours after GL-52 cadence due timestamp (default: 24).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-refresh-interval-hours",
        type=float,
        default=24.0,
        help="GL-52 acknowledgement-closure cadence refresh interval (hours).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-overdue-stalled-cycles",
        type=int,
        default=2,
        help="GL-52 overdue stalled cycle threshold (default: 2).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-52 acknowledgement-closure cadence evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-refresh-interval-hours",
        type=float,
        default=24.0,
        help="GL-48 closure cadence refresh interval (hours).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-overdue-stalled-cycles",
        type=int,
        default=2,
        help="GL-48 overdue stalled cycle threshold (default: 2).",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-48 closure cadence evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-49 closure-cadence escalation evaluation.",
    )
    parser.add_argument(
        "--backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalate-after-due-hours",
        type=float,
        default=24.0,
        help="GL-49 escalation threshold hours after cadence due timestamp (default: 24).",
    )
    parser.add_argument(
        "--backfill-submission-queue-refresh-interval-hours",
        type=float,
        default=24.0,
        help="GL-37 evidence refresh cadence interval (hours).",
    )
    parser.add_argument(
        "--backfill-submission-queue-now-utc",
        default="",
        help="Optional UTC timestamp for deterministic GL-37 cadence evaluation.",
    )
    parser.add_argument("--backfill-submission-owner", default="controlled-beta-ops")
    parser.add_argument("--backfill-handoff-output", default=str(DEFAULT_BACKFILL_HANDOFF_REPORT))
    parser.add_argument("--backfill-handoff-summary-output", default=str(DEFAULT_BACKFILL_HANDOFF_SUMMARY))
    parser.add_argument("--backfill-handoff-owner", default="controlled-beta-ops")
    parser.add_argument(
        "--backfill-handoff-escalations-output",
        default=str(DEFAULT_BACKFILL_HANDOFF_ESCALATIONS_REPORT),
    )
    parser.add_argument(
        "--backfill-handoff-escalations-summary-output",
        default=str(DEFAULT_BACKFILL_HANDOFF_ESCALATIONS_SUMMARY),
    )
    parser.add_argument("--backfill-handoff-escalations-owner", default="controlled-beta-ops")
    parser.add_argument(
        "--backfill-handoff-pending-ack-sla-hours",
        type=float,
        default=24.0,
        help="SLA threshold (hours) for GL-26 pending-ack aging diagnostics.",
    )
    parser.add_argument(
        "--backfill-handoff-pending-ack-overdue-hours",
        type=float,
        default=72.0,
        help="Overdue escalation threshold (hours) for GL-26 pending-ack aging diagnostics.",
    )
    parser.add_argument(
        "--backfill-handoff-now-utc",
        default="",
        help=(
            "Optional UTC timestamp passed to GL-24/GL-26 handoff stage for deterministic "
            "ack aging evaluation."
        ),
    )
    parser.add_argument(
        "--backfill-handoff-acknowledgements-report",
        default="",
        help=(
            "Optional operator acknowledgement report for GL-25 linkage closure. "
            "When provided, GL-24 handoff closure requires submission + acknowledgement match."
        ),
    )
    parser.add_argument("--trial-metrics-report-output", default=str(DEFAULT_TRIAL_METRICS_REPORT))
    parser.add_argument("--trial-metrics-summary-output", default=str(DEFAULT_TRIAL_METRICS_SUMMARY))
    parser.add_argument("--launch-readiness-output", default=str(DEFAULT_LAUNCH_READINESS_REPORT))
    parser.add_argument("--launch-readiness-summary-output", default=str(DEFAULT_LAUNCH_READINESS_SUMMARY))
    parser.add_argument("--release-switch-report", default=str(DEFAULT_RELEASE_SWITCH_REPORT))
    parser.add_argument("--current-status-doc", default=str(DEFAULT_CURRENT_STATUS_DOC))
    parser.add_argument(
        "--controlled-trial-run-report",
        default="",
        help=(
            "Run report path passed to launch-readiness gate security fallback. "
            "Defaults to first --run-report entry."
        ),
    )
    parser.add_argument("--agent-smoke-report", default=str(DEFAULT_AGENT_SMOKE_REPORT))
    parser.add_argument("--security-gate-report", default="")
    parser.add_argument("--doc-sync-report", default=str(DEFAULT_DOC_SYNC_REPORT))
    parser.add_argument("--operations-readiness-report", default=str(DEFAULT_OPERATIONS_READINESS_REPORT))
    parser.add_argument("--evidence-pack-output", default=str(DEFAULT_EVIDENCE_PACK))
    parser.add_argument("--manifest-preflight-report", default=str(DEFAULT_MANIFEST_PREFLIGHT_REPORT))
    parser.add_argument("--manifest-preflight-summary", default=str(DEFAULT_MANIFEST_PREFLIGHT_SUMMARY))
    parser.add_argument("--run-doc-sync", dest="run_doc_sync", action="store_true", default=True)
    parser.add_argument("--no-run-doc-sync", dest="run_doc_sync", action="store_false")
    parser.add_argument("--minimum-complete-loops", type=int, default=10)
    parser.add_argument("--minimum-modalities", type=int, default=4)
    parser.add_argument("--release-decision", choices=("GO", "HOLD"), default="GO")
    parser.add_argument("--operator-cost-accepted", choices=("true", "false"), default="true")
    parser.add_argument("--max-evidence-age-hours", type=float, default=336.0)
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--fail-on-blocker", action="store_true")
    parser.add_argument("--fail-on-hold", action="store_true")
    args = parser.parse_args()
    _apply_windows_output_path_aliases(args)
    return args


def _resolve_required_output_path(value: str, *, name: str) -> Path:
    cleaned = str(value or "").strip()
    if not cleaned or cleaned == "-":
        raise ValueError("%s cannot be empty or '-' for launch-evidence pipeline." % name)
    return Path(cleaned).resolve()


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _path_for_io(path: Path) -> Path:
    resolved = path.resolve()
    if os.name != "nt":
        return resolved
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return Path(text)
    if text.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + text[2:])
    return Path("\\\\?\\" + text)


def _maybe_windows_shorten_output_path(raw_value: str, *, label: str) -> str:
    resolved = Path(str(raw_value).strip()).resolve()
    if os.name != "nt":
        return str(resolved)
    if len(str(resolved)) <= 248:
        return str(resolved)

    suffix = resolved.suffix
    if not suffix:
        suffix = ".md" if "summary" in label else ".json"

    normalized_label = (
        label.replace("_summary_output", "")
        .replace("_manifest_output", "")
        .replace("_template_output", "")
        .replace("_output", "")
        .replace("_", "-")
    )
    normalized_label = "".join(ch for ch in normalized_label if ch.isalnum() or ch == "-").strip("-")
    if not normalized_label:
        normalized_label = "gl13-output"
    normalized_label = normalized_label[:28]
    digest = hashlib.sha1(f"{label}:{resolved}".encode("utf-8")).hexdigest()[:10]
    alias = resolved.parent / f"{normalized_label}-{digest}{suffix}"
    if len(str(alias)) > 248:
        alias = resolved.parent / f"gl13-{digest}{suffix}"
    return str(alias)


def _apply_windows_output_path_aliases(args: argparse.Namespace) -> None:
    if os.name != "nt":
        return
    output_suffixes = (
        "_output",
        "_summary_output",
        "_manifest_output",
        "_template_output",
    )
    for attr_name, attr_value in vars(args).items():
        if not attr_name.endswith(output_suffixes):
            continue
        if not isinstance(attr_value, str):
            continue
        cleaned = attr_value.strip()
        if not cleaned or cleaned == "-":
            continue
        setattr(
            args,
            attr_name,
            _maybe_windows_shorten_output_path(cleaned, label=attr_name),
        )


def _is_default_cli_path(*, raw_value: str, default_path: Path, label: str) -> bool:
    resolved_default = default_path.resolve()
    resolved_value = Path(str(raw_value).strip()).resolve()
    if resolved_value == resolved_default:
        return True
    # On Windows, parser-level long-path aliases must remain sticky. Treating an
    # alias as the original default expands it back to an overlong path in later
    # derived stages, and downstream scripts then fail regular Path.is_file checks.
    return False


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(_path_for_io(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object: %s" % path)
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    io_path = _path_for_io(path)
    io_path.parent.mkdir(parents=True, exist_ok=True)
    io_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _print_command_output(prefix: str, result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout.strip():
        print("%s stdout:\n%s" % (prefix, result.stdout.rstrip()))
    if result.stderr.strip():
        print("%s stderr:\n%s" % (prefix, result.stderr.rstrip()), file=sys.stderr)


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _to_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return float(default)


def _resolve_loop_manifest_paths(
    *,
    explicit_paths: list[str],
    manifest_dirs: list[str],
    pattern: str,
    recursive: bool,
) -> tuple[list[Path], list[Path]]:
    resolved_explicit_paths = [Path(item).resolve() for item in explicit_paths if str(item).strip()]
    resolved_manifest_dirs = [Path(item).resolve() for item in manifest_dirs if str(item).strip()]

    discovered_from_dirs: list[Path] = []
    normalized_pattern = str(pattern or "").strip() or "*.json"
    for directory in resolved_manifest_dirs:
        if not directory.is_dir():
            raise ValueError("Loop manifest directory does not exist or is not a directory: %s" % directory)
        iterator = directory.rglob(normalized_pattern) if recursive else directory.glob(normalized_pattern)
        discovered_from_dirs.extend(path.resolve() for path in iterator if path.is_file())

    deduped_paths: dict[str, Path] = {}
    for path in resolved_explicit_paths:
        deduped_paths[str(path)] = path
    for path in sorted(discovered_from_dirs, key=lambda value: str(value)):
        deduped_paths[str(path)] = path
    return list(deduped_paths.values()), resolved_manifest_dirs


def _format_no_loop_manifest_matches_message(
    *,
    manifest_dirs: list[Path],
    pattern: str,
    recursive: bool,
) -> str:
    directory_text = ", ".join(str(path) for path in manifest_dirs) if manifest_dirs else "none"
    normalized_pattern = str(pattern or "").strip() or "*.json"
    return (
        "no loop manifest JSON files matched explicit loop evidence input(s): "
        "directories=%s pattern=%s recursive=%s. "
        "Add at least one JSON manifest with top-level 'loops', or pass --run-report for run-report input."
        % (directory_text, normalized_pattern, str(bool(recursive)).lower())
    )


def _build_collection_command(
    args: argparse.Namespace,
    run_reports: list[Path],
    manifest_output: Path,
    *,
    extra_loop_manifest_paths: list[Path] | None = None,
) -> list[str]:
    command = [
        sys.executable,
        str(REAL_LOOP_COLLECTION_SCRIPT),
    ]
    for path in run_reports:
        command.extend(["--run-report", str(path)])
    combined_loop_manifest_paths: list[Path] = []
    for value in args.loop_manifest:
        item = str(value).strip()
        if item:
            combined_loop_manifest_paths.append(Path(item).resolve())
    if extra_loop_manifest_paths:
        combined_loop_manifest_paths.extend(path.resolve() for path in extra_loop_manifest_paths if str(path).strip())
    deduped_loop_manifest_paths: dict[str, Path] = {}
    for path in combined_loop_manifest_paths:
        deduped_loop_manifest_paths[str(path)] = path
    for path in deduped_loop_manifest_paths.values():
        command.extend(["--loop-manifest", str(path)])
    for value in args.loop_manifest_dir:
        item = str(value).strip()
        if item:
            command.extend(["--loop-manifest-dir", str(Path(item).resolve())])
    pattern = str(args.loop_manifest_pattern).strip()
    if pattern:
        command.extend(["--loop-manifest-pattern", pattern])
    if bool(args.loop_manifest_recursive):
        command.append("--loop-manifest-recursive")
    if bool(args.strict_loop_manifest_contract):
        command.append("--strict-loop-manifest-contract")
    command.extend(
        [
            "--output",
            str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
            "--summary-output",
            str(args.collection_summary_output),
            "--manifest-output",
            str(manifest_output),
            "--backfill-plan-output",
            str(args.backfill_plan_output),
            "--minimum-complete-loops",
            str(max(1, int(args.minimum_complete_loops))),
            "--minimum-modalities",
            str(max(1, int(args.minimum_modalities))),
            "--release-decision",
            str(args.release_decision).strip().upper(),
            "--operator-cost-accepted",
            str(args.operator_cost_accepted).strip().lower(),
        ]
    )
    if args.fail_on_blocker:
        command.append("--fail-on-blocker")
    return command


def _build_trial_metrics_command(args: argparse.Namespace, manifest_path: Path, report_output: Path) -> list[str]:
    return [
        sys.executable,
        str(TRIAL_METRICS_COLLECTOR_SCRIPT),
        "--manifest",
        str(manifest_path),
        "--output",
        str(report_output),
        "--summary-output",
        str(args.trial_metrics_summary_output),
        "--minimum-complete-loops",
        str(max(1, int(args.minimum_complete_loops))),
        "--minimum-modalities",
        str(max(1, int(args.minimum_modalities))),
    ]


def _build_backfill_execution_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(REAL_LOOP_BACKFILL_EXECUTION_SCRIPT),
        "--backfill-plan",
        str(Path(args.backfill_plan_output).resolve()),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--output",
        str(Path(args.backfill_execution_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_execution_summary_output).resolve()),
    ]


def _build_backfill_intake_actions_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(REAL_LOOP_BACKFILL_INTAKE_ACTIONS_SCRIPT),
        "--backfill-plan",
        str(Path(args.backfill_plan_output).resolve()),
        "--backfill-execution-report",
        str(Path(args.backfill_execution_output).resolve()),
        "--output",
        str(Path(args.backfill_intake_actions_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_intake_actions_summary_output).resolve()),
        "--owner",
        str(args.backfill_intake_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_templates_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(REAL_LOOP_BACKFILL_SUBMISSION_TEMPLATES_SCRIPT),
        "--intake-actions-report",
        str(Path(args.backfill_intake_actions_output).resolve()),
        "--output",
        str(Path(args.backfill_submission_templates_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_submission_templates_summary_output).resolve()),
        "--manifest-template-output",
        str(Path(args.backfill_submission_manifest_template_output).resolve()),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_consumption_command(args: argparse.Namespace) -> list[str]:
    template_manifest_output_path = Path(args.backfill_submission_manifest_template_output).resolve()
    template_output_dir = template_manifest_output_path.parent

    default_real_inputs_path = DEFAULT_BACKFILL_SUBMISSION_REAL_INPUTS.resolve()
    configured_real_inputs_path = Path(args.backfill_submission_real_inputs).resolve()
    real_inputs_path = (
        template_output_dir / default_real_inputs_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_real_inputs,
            default_path=default_real_inputs_path,
            label="backfill_submission_real_inputs",
        )
        else configured_real_inputs_path
    )
    if not real_inputs_path.is_file():
        real_inputs_path.parent.mkdir(parents=True, exist_ok=True)
        real_inputs_path.write_text(
            json.dumps(
                {
                    "schema_version": "real_trial_backfill_submission_real_inputs.v1",
                    "generated_at_utc": datetime.now(timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "owner": str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
                    "description": (
                        "Autogenerated placeholder for GL-33 submission consumption. "
                        "Provide real submission rows in submissions[] to consume GL-31 templates."
                    ),
                    "submissions": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    default_consumption_output_path = DEFAULT_BACKFILL_SUBMISSION_CONSUMPTION_REPORT.resolve()
    configured_consumption_output_path = Path(args.backfill_submission_consumption_output).resolve()
    consumption_output_path = (
        template_output_dir / default_consumption_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_consumption_output,
            default_path=default_consumption_output_path,
            label="backfill_submission_consumption_output",
        )
        else configured_consumption_output_path
    )

    default_consumption_summary_output_path = DEFAULT_BACKFILL_SUBMISSION_CONSUMPTION_SUMMARY.resolve()
    configured_consumption_summary_output_path = Path(args.backfill_submission_consumption_summary_output).resolve()
    consumption_summary_output_path = (
        template_output_dir / default_consumption_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_consumption_summary_output,
            default_path=default_consumption_summary_output_path,
            label="backfill_submission_consumption_summary_output",
        )
        else configured_consumption_summary_output_path
    )

    default_consumed_manifest_output_path = DEFAULT_BACKFILL_SUBMISSION_CONSUMED_MANIFEST.resolve()
    configured_consumed_manifest_output_path = Path(args.backfill_submission_consumed_manifest_output).resolve()
    consumed_manifest_output_path = (
        template_output_dir / default_consumed_manifest_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_consumed_manifest_output,
            default_path=default_consumed_manifest_output_path,
            label="backfill_submission_consumed_manifest_output",
        )
        else configured_consumed_manifest_output_path
    )

    args.backfill_submission_real_inputs = str(real_inputs_path)
    args.backfill_submission_consumption_output = str(consumption_output_path)
    args.backfill_submission_consumption_summary_output = str(consumption_summary_output_path)
    args.backfill_submission_consumed_manifest_output = str(consumed_manifest_output_path)

    return [
        sys.executable,
        str(REAL_LOOP_BACKFILL_SUBMISSION_CONSUMPTION_SCRIPT),
        "--submission-manifest-template",
        str(template_manifest_output_path),
        "--real-submissions-input",
        str(real_inputs_path),
        "--output",
        str(consumption_output_path),
        "--summary-output",
        str(consumption_summary_output_path),
        "--consumed-manifest-output",
        str(consumed_manifest_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_throughput_command(args: argparse.Namespace) -> list[str]:
    default_throughput_output_path = DEFAULT_BACKFILL_SUBMISSION_THROUGHPUT_REPORT.resolve()
    configured_throughput_output_path = Path(args.backfill_submission_throughput_output).resolve()
    throughput_output_path = (
        Path(args.backfill_submission_consumption_output).resolve().parent / default_throughput_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_throughput_output,
            default_path=default_throughput_output_path,
            label="backfill_submission_throughput_output",
        )
        else configured_throughput_output_path
    )

    default_throughput_summary_output_path = DEFAULT_BACKFILL_SUBMISSION_THROUGHPUT_SUMMARY.resolve()
    configured_throughput_summary_output_path = Path(args.backfill_submission_throughput_summary_output).resolve()
    throughput_summary_output_path = (
        Path(args.backfill_submission_consumption_summary_output).resolve().parent
        / default_throughput_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_throughput_summary_output,
            default_path=default_throughput_summary_output_path,
            label="backfill_submission_throughput_summary_output",
        )
        else configured_throughput_summary_output_path
    )

    args.backfill_submission_throughput_output = str(throughput_output_path)
    args.backfill_submission_throughput_summary_output = str(throughput_summary_output_path)

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_THROUGHPUT_SCRIPT),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--backfill-execution-report",
        str(Path(args.backfill_execution_output).resolve()),
        "--backfill-submission-consumption-report",
        str(Path(args.backfill_submission_consumption_output).resolve()),
        "--output",
        str(throughput_output_path),
        "--summary-output",
        str(throughput_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_command(args: argparse.Namespace) -> list[str]:
    default_queue_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_REPORT.resolve()
    configured_queue_output_path = Path(args.backfill_submission_queue_output).resolve()
    queue_output_path = (
        Path(args.backfill_submission_throughput_output).resolve().parent / default_queue_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_output,
            default_path=default_queue_output_path,
            label="backfill_submission_queue_output",
        )
        else configured_queue_output_path
    )

    default_queue_summary_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_SUMMARY.resolve()
    configured_queue_summary_output_path = Path(args.backfill_submission_queue_summary_output).resolve()
    queue_summary_output_path = (
        Path(args.backfill_submission_throughput_summary_output).resolve().parent
        / default_queue_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_summary_output,
            default_path=default_queue_summary_output_path,
            label="backfill_submission_queue_summary_output",
        )
        else configured_queue_summary_output_path
    )

    args.backfill_submission_queue_output = str(queue_output_path)
    args.backfill_submission_queue_summary_output = str(queue_summary_output_path)

    command = [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_SCRIPT),
        "--throughput-report",
        str(Path(args.backfill_submission_throughput_output).resolve()),
        "--output",
        str(queue_output_path),
        "--summary-output",
        str(queue_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--refresh-interval-hours",
        str(float(args.backfill_submission_queue_refresh_interval_hours)),
    ]
    now_utc = str(args.backfill_submission_queue_now_utc).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command


def _build_backfill_submission_queue_completion_command(args: argparse.Namespace) -> list[str]:
    default_completion_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMPLETION_REPORT.resolve()
    configured_completion_output_path = Path(args.backfill_submission_queue_completion_output).resolve()
    completion_output_path = (
        Path(args.backfill_submission_queue_output).resolve().parent / default_completion_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_completion_output,
            default_path=default_completion_output_path,
            label="backfill_submission_queue_completion_output",
        )
        else configured_completion_output_path
    )

    default_completion_summary_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMPLETION_SUMMARY.resolve()
    configured_completion_summary_output_path = Path(
        args.backfill_submission_queue_completion_summary_output
    ).resolve()
    completion_summary_output_path = (
        Path(args.backfill_submission_queue_summary_output).resolve().parent
        / default_completion_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_completion_summary_output,
            default_path=default_completion_summary_output_path,
            label="backfill_submission_queue_completion_summary_output",
        )
        else configured_completion_summary_output_path
    )

    args.backfill_submission_queue_completion_output = str(completion_output_path)
    args.backfill_submission_queue_completion_summary_output = str(completion_summary_output_path)

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_COMPLETION_SCRIPT),
        "--submission-queue-report",
        str(Path(args.backfill_submission_queue_output).resolve()),
        "--submission-throughput-report",
        str(Path(args.backfill_submission_throughput_output).resolve()),
        "--handoff-report",
        str(Path(args.backfill_handoff_output).resolve()),
        "--output",
        str(completion_output_path),
        "--summary-output",
        str(completion_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_commitments_command(args: argparse.Namespace) -> list[str]:
    default_commitments_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENTS_REPORT.resolve()
    configured_commitments_output_path = Path(args.backfill_submission_queue_commitments_output).resolve()
    commitments_output_path = (
        Path(args.backfill_submission_queue_completion_output).resolve().parent / default_commitments_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_commitments_output,
            default_path=default_commitments_output_path,
            label="backfill_submission_queue_commitments_output",
        )
        else configured_commitments_output_path
    )

    default_commitments_summary_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENTS_SUMMARY.resolve()
    configured_commitments_summary_output_path = Path(
        args.backfill_submission_queue_commitments_summary_output
    ).resolve()
    commitments_summary_output_path = (
        Path(args.backfill_submission_queue_completion_summary_output).resolve().parent
        / default_commitments_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_commitments_summary_output,
            default_path=default_commitments_summary_output_path,
            label="backfill_submission_queue_commitments_summary_output",
        )
        else configured_commitments_summary_output_path
    )

    args.backfill_submission_queue_commitments_output = str(commitments_output_path)
    args.backfill_submission_queue_commitments_summary_output = str(commitments_summary_output_path)

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_COMMITMENTS_SCRIPT),
        "--submission-queue-report",
        str(Path(args.backfill_submission_queue_output).resolve()),
        "--submission-queue-completion-report",
        str(Path(args.backfill_submission_queue_completion_output).resolve()),
        "--handoff-escalations-report",
        str(Path(args.backfill_handoff_escalations_output).resolve()),
        "--submission-throughput-report",
        str(Path(args.backfill_submission_throughput_output).resolve()),
        "--output",
        str(commitments_output_path),
        "--summary-output",
        str(commitments_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_commitment_closure_command(args: argparse.Namespace) -> list[str]:
    default_closure_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_REPORT.resolve()
    configured_closure_output_path = Path(
        args.backfill_submission_queue_commitment_closure_output
    ).resolve()
    closure_output_path = (
        Path(args.backfill_submission_queue_commitments_output).resolve().parent
        / default_closure_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_commitment_closure_output,
            default_path=default_closure_output_path,
            label="backfill_submission_queue_commitment_closure_output",
        )
        else configured_closure_output_path
    )

    default_closure_summary_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_SUMMARY.resolve()
    configured_closure_summary_output_path = Path(
        args.backfill_submission_queue_commitment_closure_summary_output
    ).resolve()
    closure_summary_output_path = (
        Path(args.backfill_submission_queue_commitments_summary_output).resolve().parent
        / default_closure_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_commitment_closure_summary_output,
            default_path=default_closure_summary_output_path,
            label="backfill_submission_queue_commitment_closure_summary_output",
        )
        else configured_closure_summary_output_path
    )

    args.backfill_submission_queue_commitment_closure_output = str(closure_output_path)
    args.backfill_submission_queue_commitment_closure_summary_output = str(closure_summary_output_path)

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_COMMITMENT_CLOSURE_SCRIPT),
        "--submission-queue-commitments-report",
        str(Path(args.backfill_submission_queue_commitments_output).resolve()),
        "--submission-queue-completion-report",
        str(Path(args.backfill_submission_queue_completion_output).resolve()),
        "--output",
        str(closure_output_path),
        "--summary-output",
        str(closure_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_followup_command(args: argparse.Namespace) -> list[str]:
    default_followup_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_REPORT.resolve()
    configured_followup_output_path = Path(args.backfill_submission_queue_followup_output).resolve()
    followup_output_path = (
        Path(args.backfill_submission_queue_commitment_closure_output).resolve().parent
        / default_followup_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_output,
            default_path=default_followup_output_path,
            label="backfill_submission_queue_followup_output",
        )
        else configured_followup_output_path
    )

    default_followup_summary_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_SUMMARY.resolve()
    configured_followup_summary_output_path = Path(args.backfill_submission_queue_followup_summary_output).resolve()
    followup_summary_output_path = (
        Path(args.backfill_submission_queue_commitment_closure_summary_output).resolve().parent
        / default_followup_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_summary_output,
            default_path=default_followup_summary_output_path,
            label="backfill_submission_queue_followup_summary_output",
        )
        else configured_followup_summary_output_path
    )

    args.backfill_submission_queue_followup_output = str(followup_output_path)
    args.backfill_submission_queue_followup_summary_output = str(followup_summary_output_path)

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_SCRIPT),
        "--submission-queue-commitment-closure-report",
        str(Path(args.backfill_submission_queue_commitment_closure_output).resolve()),
        "--output",
        str(followup_output_path),
        "--summary-output",
        str(followup_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_followup_resolution_command(args: argparse.Namespace) -> list[str]:
    default_resolution_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_REPORT.resolve()
    configured_resolution_output_path = Path(
        args.backfill_submission_queue_followup_resolution_output
    ).resolve()
    resolution_output_path = (
        Path(args.backfill_submission_queue_followup_output).resolve().parent
        / default_resolution_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_output,
            default_path=default_resolution_output_path,
            label="backfill_submission_queue_followup_resolution_output",
        )
        else configured_resolution_output_path
    )

    default_resolution_summary_output_path = DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_SUMMARY.resolve()
    configured_resolution_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_summary_output
    ).resolve()
    resolution_summary_output_path = (
        Path(args.backfill_submission_queue_followup_summary_output).resolve().parent
        / default_resolution_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_summary_output,
            default_path=default_resolution_summary_output_path,
            label="backfill_submission_queue_followup_resolution_summary_output",
        )
        else configured_resolution_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_output = str(resolution_output_path)
    args.backfill_submission_queue_followup_resolution_summary_output = str(resolution_summary_output_path)

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_SCRIPT),
        "--submission-queue-followup-report",
        str(Path(args.backfill_submission_queue_followup_output).resolve()),
        "--handoff-report",
        str(Path(args.backfill_handoff_output).resolve()),
        "--backfill-submission-consumption-report",
        str(Path(args.backfill_submission_consumption_output).resolve()),
        "--output",
        str(resolution_output_path),
        "--summary-output",
        str(resolution_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_followup_resolution_escalations_command(
    args: argparse.Namespace,
) -> list[str]:
    default_escalations_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_REPORT.resolve()
    )
    configured_escalations_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalations_output
    ).resolve()
    escalations_output_path = (
        Path(args.backfill_submission_queue_followup_resolution_output).resolve().parent
        / default_escalations_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalations_output,
            default_path=default_escalations_output_path,
            label="backfill_submission_queue_followup_resolution_escalations_output",
        )
        else configured_escalations_output_path
    )

    default_escalations_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_SUMMARY.resolve()
    )
    configured_escalations_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalations_summary_output
    ).resolve()
    escalations_summary_output_path = (
        Path(args.backfill_submission_queue_followup_resolution_summary_output).resolve().parent
        / default_escalations_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalations_summary_output,
            default_path=default_escalations_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalations_summary_output",
        )
        else configured_escalations_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalations_output = str(escalations_output_path)
    args.backfill_submission_queue_followup_resolution_escalations_summary_output = str(
        escalations_summary_output_path
    )

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATIONS_SCRIPT),
        "--submission-queue-followup-resolution-report",
        str(Path(args.backfill_submission_queue_followup_resolution_output).resolve()),
        "--submission-queue-followup-report",
        str(Path(args.backfill_submission_queue_followup_output).resolve()),
        "--output",
        str(escalations_output_path),
        "--summary-output",
        str(escalations_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_followup_resolution_escalation_acknowledgements_command(
    args: argparse.Namespace,
) -> list[str]:
    default_ack_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACKNOWLEDGEMENTS_REPORT.resolve()
    )
    configured_ack_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_output
    ).resolve()
    ack_output_path = (
        Path(args.backfill_submission_queue_followup_resolution_escalations_output).resolve().parent
        / default_ack_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_output,
            default_path=default_ack_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_acknowledgements_output",
        )
        else configured_ack_output_path
    )

    default_ack_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACKNOWLEDGEMENTS_SUMMARY.resolve()
    )
    configured_ack_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_summary_output
    ).resolve()
    ack_summary_output_path = (
        Path(args.backfill_submission_queue_followup_resolution_escalations_summary_output).resolve().parent
        / default_ack_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_summary_output,
            default_path=default_ack_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_acknowledgements_summary_output",
        )
        else configured_ack_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_output = str(
        ack_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_summary_output = str(
        ack_summary_output_path
    )

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACKNOWLEDGEMENTS_SCRIPT),
        "--submission-queue-followup-resolution-escalations-report",
        str(Path(args.backfill_submission_queue_followup_resolution_escalations_output).resolve()),
        "--handoff-report",
        str(Path(args.backfill_handoff_output).resolve()),
        "--output",
        str(ack_output_path),
        "--summary-output",
        str(ack_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_followup_resolution_escalation_throughput_command(
    args: argparse.Namespace,
) -> list[str]:
    default_throughput_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_THROUGHPUT_REPORT.resolve()
    )
    configured_throughput_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_throughput_output
    ).resolve()
    throughput_output_path = (
        Path(args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_output).resolve().parent
        / default_throughput_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_throughput_output,
            default_path=default_throughput_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_throughput_output",
        )
        else configured_throughput_output_path
    )

    default_throughput_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_THROUGHPUT_SUMMARY.resolve()
    )
    configured_throughput_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_throughput_summary_output
    ).resolve()
    throughput_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_summary_output
        ).resolve().parent
        / default_throughput_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_throughput_summary_output,
            default_path=default_throughput_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_throughput_summary_output",
        )
        else configured_throughput_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_throughput_output = str(
        throughput_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_throughput_summary_output = str(
        throughput_summary_output_path
    )

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_THROUGHPUT_SCRIPT),
        "--submission-queue-followup-resolution-escalation-acknowledgements-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_output
            ).resolve()
        ),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--output",
        str(throughput_output_path),
        "--summary-output",
        str(throughput_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_command(
    args: argparse.Namespace,
) -> list[str]:
    default_action_plan_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_REPORT.resolve()
    )
    configured_action_plan_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_output
    ).resolve()
    action_plan_output_path = (
        Path(args.backfill_submission_queue_followup_resolution_escalation_throughput_output).resolve().parent
        / default_action_plan_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_output,
            default_path=default_action_plan_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_output",
        )
        else configured_action_plan_output_path
    )

    default_action_plan_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_SUMMARY.resolve()
    )
    configured_action_plan_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_summary_output
    ).resolve()
    action_plan_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_throughput_summary_output
        ).resolve().parent
        / default_action_plan_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_summary_output,
            default_path=default_action_plan_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_summary_output",
        )
        else configured_action_plan_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_output = str(
        action_plan_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_summary_output = str(
        action_plan_summary_output_path
    )

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_SCRIPT),
        "--submission-queue-followup-resolution-escalation-throughput-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_throughput_output
            ).resolve()
        ),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--output",
        str(action_plan_output_path),
        "--summary-output",
        str(action_plan_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_command(
    args: argparse.Namespace,
) -> list[str]:
    default_closure_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_REPORT.resolve()
    )
    configured_closure_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_output
    ).resolve()
    closure_output_path = (
        Path(args.backfill_submission_queue_followup_resolution_escalation_action_plan_output).resolve().parent
        / default_closure_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_output,
            default_path=default_closure_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_output",
        )
        else configured_closure_output_path
    )

    default_closure_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_SUMMARY.resolve()
    )
    configured_closure_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_summary_output
    ).resolve()
    closure_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_summary_output
        ).resolve().parent
        / default_closure_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_summary_output,
            default_path=default_closure_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_summary_output",
        )
        else configured_closure_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_output = str(
        closure_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_summary_output = str(
        closure_summary_output_path
    )

    return [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_SCRIPT),
        "--submission-queue-followup-resolution-escalation-action-plan-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_output
            ).resolve()
        ),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--output",
        str(closure_output_path),
        "--summary-output",
        str(closure_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_command(
    args: argparse.Namespace,
) -> list[str]:
    default_cadence_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_REPORT.resolve()
    )
    configured_cadence_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_output
    ).resolve()
    cadence_output_path = (
        Path(args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_output).resolve().parent
        / default_cadence_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_output,
            default_path=default_cadence_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_output",
        )
        else configured_cadence_output_path
    )

    default_cadence_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_SUMMARY.resolve()
    )
    configured_cadence_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_summary_output
    ).resolve()
    cadence_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_summary_output
        ).resolve().parent
        / default_cadence_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_summary_output,
            default_path=default_cadence_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_summary_output",
        )
        else configured_cadence_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_output = str(
        cadence_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_summary_output = str(
        cadence_summary_output_path
    )

    command = [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_SCRIPT),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_output
            ).resolve()
        ),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--output",
        str(cadence_output_path),
        "--summary-output",
        str(cadence_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--refresh-interval-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh_interval_hours
            )
        ),
        "--overdue-stalled-cycles",
        str(
            int(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_overdue_stalled_cycles
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_command(
    args: argparse.Namespace,
) -> list[str]:
    default_escalations_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATIONS_REPORT.resolve()
    )
    configured_escalations_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_output
    ).resolve()
    escalations_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_output
        ).resolve().parent
        / default_escalations_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_output,
            default_path=default_escalations_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_output",
        )
        else configured_escalations_output_path
    )

    default_escalations_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATIONS_SUMMARY.resolve()
    )
    configured_escalations_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_summary_output
    ).resolve()
    escalations_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_summary_output
        ).resolve().parent
        / default_escalations_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_summary_output,
            default_path=default_escalations_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_summary_output",
        )
        else configured_escalations_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_output = str(
        escalations_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_summary_output = str(
        escalations_summary_output_path
    )

    command = [
        sys.executable,
        str(REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATIONS_SCRIPT),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_output
            ).resolve()
        ),
        "--output",
        str(escalations_output_path),
        "--summary-output",
        str(escalations_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--escalate-after-due-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalate_after_due_hours
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_command(
    args: argparse.Namespace,
) -> list[str]:
    default_ingestion_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_INGESTION_REPORT.resolve()
    )
    configured_ingestion_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_output
    ).resolve()
    ingestion_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_output
        ).resolve().parent
        / default_ingestion_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_output,
            default_path=default_ingestion_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_output",
        )
        else configured_ingestion_output_path
    )

    default_ingestion_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_INGESTION_SUMMARY.resolve()
    )
    configured_ingestion_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_summary_output
    ).resolve()
    ingestion_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_summary_output
        ).resolve().parent
        / default_ingestion_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_summary_output,
            default_path=default_ingestion_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_summary_output",
        )
        else configured_ingestion_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_output = str(
        ingestion_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_summary_output = str(
        ingestion_summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_INGESTION_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_output
            ).resolve()
        ),
        "--handoff-report",
        str(Path(args.backfill_handoff_output).resolve()),
        "--output",
        str(ingestion_output_path),
        "--summary-output",
        str(ingestion_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]
    ack_report = str(args.backfill_handoff_acknowledgements_report).strip()
    if ack_report:
        command.extend(["--acknowledgements-report", str(Path(ack_report).resolve())])
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_command(
    args: argparse.Namespace,
) -> list[str]:
    default_closure_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_REPORT.resolve()
    )
    configured_closure_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_output
    ).resolve()
    closure_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_output
        ).resolve().parent
        / default_closure_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_output,
            default_path=default_closure_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_output",
        )
        else configured_closure_output_path
    )

    default_closure_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_SUMMARY.resolve()
    )
    configured_closure_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_summary_output
    ).resolve()
    closure_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_summary_output
        ).resolve().parent
        / default_closure_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_summary_output,
            default_path=default_closure_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_summary_output",
        )
        else configured_closure_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_output = str(
        closure_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_summary_output = str(
        closure_summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_output
            ).resolve()
        ),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--output",
        str(closure_output_path),
        "--summary-output",
        str(closure_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_command(
    args: argparse.Namespace,
) -> list[str]:
    default_cadence_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_REPORT.resolve()
    )
    configured_cadence_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_output
    ).resolve()
    cadence_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_output
        ).resolve().parent
        / default_cadence_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_output,
            default_path=default_cadence_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_output",
        )
        else configured_cadence_output_path
    )

    default_cadence_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_SUMMARY.resolve()
    )
    configured_cadence_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_summary_output
    ).resolve()
    cadence_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_summary_output
        ).resolve().parent
        / default_cadence_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_summary_output,
            default_path=default_cadence_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_summary_output",
        )
        else configured_cadence_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_output = str(
        cadence_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_summary_output = str(
        cadence_summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_output
            ).resolve()
        ),
        "--output",
        str(cadence_output_path),
        "--summary-output",
        str(cadence_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--refresh-interval-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh_interval_hours
            )
        ),
        "--overdue-stalled-cycles",
        str(
            int(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_overdue_stalled_cycles
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_command(
    args: argparse.Namespace,
) -> list[str]:
    default_escalations_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATIONS_REPORT.resolve()
    )
    configured_escalations_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_output
    ).resolve()
    escalations_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_output
        ).resolve().parent
        / default_escalations_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_output,
            default_path=default_escalations_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_output",
        )
        else configured_escalations_output_path
    )

    default_escalations_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATIONS_SUMMARY.resolve()
    )
    configured_escalations_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_summary_output
    ).resolve()
    escalations_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_summary_output
        ).resolve().parent
        / default_escalations_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_summary_output,
            default_path=default_escalations_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_summary_output",
        )
        else configured_escalations_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_output = str(
        escalations_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_summary_output = str(
        escalations_summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATIONS_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_output
            ).resolve()
        ),
        "--output",
        str(escalations_output_path),
        "--summary-output",
        str(escalations_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--escalate-after-due-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalate_after_due_hours
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_command(
    args: argparse.Namespace,
) -> list[str]:
    default_closure_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_REPORT.resolve()
    )
    configured_closure_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_output
    ).resolve()
    closure_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_output
        ).resolve().parent
        / default_closure_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_output,
            default_path=default_closure_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_output",
        )
        else configured_closure_output_path
    )

    default_closure_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_SUMMARY.resolve()
    )
    configured_closure_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_summary_output
    ).resolve()
    closure_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_summary_output
        ).resolve().parent
        / default_closure_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_summary_output,
            default_path=default_closure_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_summary_output",
        )
        else configured_closure_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_output = str(
        closure_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_summary_output = str(
        closure_summary_output_path
    )

    return [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_output
            ).resolve()
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_output
            ).resolve()
        ),
        "--output",
        str(closure_output_path),
        "--summary-output",
        str(closure_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_command(
    args: argparse.Namespace,
) -> list[str]:
    default_cadence_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_REPORT.resolve()
    )
    configured_cadence_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_output
    ).resolve()
    cadence_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_output
        ).resolve().parent
        / default_cadence_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_output,
            default_path=default_cadence_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_output",
        )
        else configured_cadence_output_path
    )

    default_cadence_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SUMMARY.resolve()
    )
    configured_cadence_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_summary_output
    ).resolve()
    cadence_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_summary_output
        ).resolve().parent
        / default_cadence_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_summary_output,
            default_path=default_cadence_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_summary_output",
        )
        else configured_cadence_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_output = str(
        cadence_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_summary_output = str(
        cadence_summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_output
            ).resolve()
        ),
        "--output",
        str(cadence_output_path),
        "--summary-output",
        str(cadence_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--refresh-interval-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh_interval_hours
            )
        ),
        "--overdue-stalled-cycles",
        str(
            int(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_command(
    args: argparse.Namespace,
) -> list[str]:
    default_escalations_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_REPORT.resolve()
    )
    configured_escalations_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_output
    ).resolve()
    escalations_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_output
        ).resolve().parent
        / default_escalations_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_output,
            default_path=default_escalations_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_output",
        )
        else configured_escalations_output_path
    )

    default_escalations_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SUMMARY.resolve()
    )
    configured_escalations_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_summary_output
    ).resolve()
    escalations_summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_summary_output
        ).resolve().parent
        / default_escalations_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_summary_output,
            default_path=default_escalations_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_summary_output",
        )
        else configured_escalations_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_output = str(
        escalations_output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_summary_output = str(
        escalations_summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_output
            ).resolve()
        ),
        "--output",
        str(escalations_output_path),
        "--summary-output",
        str(escalations_summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--escalate-after-due-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalate_after_due_hours
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_command(
    args: argparse.Namespace,
) -> list[str]:
    default_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_REPORT.resolve()
    )
    configured_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_output
    ).resolve()
    output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_output
        ).resolve().parent
        / default_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_output,
            default_path=default_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_output",
        )
        else configured_output_path
    )

    default_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SUMMARY.resolve()
    )
    configured_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output
    ).resolve()
    summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_summary_output
        ).resolve().parent
        / default_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output,
            default_path=default_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output",
        )
        else configured_summary_output_path
    )

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_output = str(
        output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output = str(
        summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_output
            ).resolve()
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_output
            ).resolve()
        ),
        "--output",
        str(output_path),
        "--summary-output",
        str(summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command(
    args: argparse.Namespace,
) -> list[str]:
    default_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_REPORT.resolve()
    )
    configured_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
    ).resolve()
    output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_output
        ).resolve().parent
        / default_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output,
            default_path=default_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output",
        )
        else configured_output_path
    )

    default_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SUMMARY.resolve()
    )
    configured_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output
    ).resolve()
    summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output
        ).resolve().parent
        / default_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output,
            default_path=default_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output",
        )
        else configured_summary_output_path
    )

    # GL-58 paths may be recomputed from parent/default filename and can exceed
    # Windows path limits; shorten deterministically when needed.
    output_path = Path(
        _maybe_windows_shorten_output_path(
            str(output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output",
        )
    ).resolve()
    summary_output_path = Path(
        _maybe_windows_shorten_output_path(
            str(summary_output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output",
        )
    ).resolve()

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output = str(
        output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output = str(
        summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_output
            ).resolve()
        ),
        "--output",
        str(output_path),
        "--summary-output",
        str(summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--refresh-interval-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh_interval_hours
            )
        ),
        "--overdue-stalled-cycles",
        str(
            int(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command(
    args: argparse.Namespace,
) -> list[str]:
    default_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_REPORT.resolve()
    )
    configured_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output
    ).resolve()
    output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
        ).resolve().parent
        / default_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output,
            default_path=default_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output",
        )
        else configured_output_path
    )

    default_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SUMMARY.resolve()
    )
    configured_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output
    ).resolve()
    summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output
        ).resolve().parent
        / default_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output,
            default_path=default_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output",
        )
        else configured_summary_output_path
    )

    # GL-59 paths may be recomputed from parent/default filename and can exceed
    # Windows path limits; shorten deterministically when needed.
    output_path = Path(
        _maybe_windows_shorten_output_path(
            str(output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output",
        )
    ).resolve()
    summary_output_path = Path(
        _maybe_windows_shorten_output_path(
            str(summary_output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output",
        )
    ).resolve()

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output = str(
        output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output = str(
        summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
            ).resolve()
        ),
        "--output",
        str(output_path),
        "--summary-output",
        str(summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--escalate-after-due-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalate_after_due_hours
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_command(
    args: argparse.Namespace,
) -> list[str]:
    default_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_REPORT.resolve()
    )
    configured_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_output
    ).resolve()
    output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output
        ).resolve().parent
        / default_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_output,
            default_path=default_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_output",
        )
        else configured_output_path
    )

    default_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SUMMARY.resolve()
    )
    configured_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output
    ).resolve()
    summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output
        ).resolve().parent
        / default_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output,
            default_path=default_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output",
        )
        else configured_summary_output_path
    )

    # GL-60 paths may be recomputed from parent/default filename and can exceed
    # Windows path limits; shorten deterministically when needed.
    output_path = Path(
        _maybe_windows_shorten_output_path(
            str(output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_output",
        )
    ).resolve()
    summary_output_path = Path(
        _maybe_windows_shorten_output_path(
            str(summary_output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output",
        )
    ).resolve()

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_output = str(output_path)
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output = str(summary_output_path)

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output
            ).resolve()
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_output
            ).resolve()
        ),
        "--output",
        str(output_path),
        "--summary-output",
        str(summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
    ]
    return command


def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command(
    args: argparse.Namespace,
) -> list[str]:
    default_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_REPORT.resolve()
    )
    configured_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
    ).resolve()
    output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_output
        ).resolve().parent
        / default_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output,
            default_path=default_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output",
        )
        else configured_output_path
    )

    default_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SUMMARY.resolve()
    )
    configured_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output
    ).resolve()
    summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output
        ).resolve().parent
        / default_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output,
            default_path=default_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output",
        )
        else configured_summary_output_path
    )

    # GL-61 paths may be recomputed from parent/default filename and can exceed
    # Windows path limits; shorten deterministically when needed.
    output_path = Path(
        _maybe_windows_shorten_output_path(
            str(output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output",
        )
    ).resolve()
    summary_output_path = Path(
        _maybe_windows_shorten_output_path(
            str(summary_output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output",
        )
    ).resolve()

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output = str(
        output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output = str(
        summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_output
            ).resolve()
        ),
        "--output",
        str(output_path),
        "--summary-output",
        str(summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--refresh-interval-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh_interval_hours
            )
        ),
        "--overdue-stalled-cycles",
        str(
            int(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command



def _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command(
    args: argparse.Namespace,
) -> list[str]:
    default_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_REPORT.resolve()
    )
    configured_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output
    ).resolve()
    output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
        ).resolve().parent
        / default_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output,
            default_path=default_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output",
        )
        else configured_output_path
    )

    default_summary_output_path = (
        DEFAULT_BACKFILL_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SUMMARY.resolve()
    )
    configured_summary_output_path = Path(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output
    ).resolve()
    summary_output_path = (
        Path(
            args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output
        ).resolve().parent
        / default_summary_output_path.name
        if _is_default_cli_path(
            raw_value=args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output,
            default_path=default_summary_output_path,
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output",
        )
        else configured_summary_output_path
    )

    # GL-62 paths may be recomputed from parent/default filename and can exceed
    # Windows path limits; shorten deterministically when needed.
    output_path = Path(
        _maybe_windows_shorten_output_path(
            str(output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output",
        )
    ).resolve()
    summary_output_path = Path(
        _maybe_windows_shorten_output_path(
            str(summary_output_path),
            label="backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output",
        )
    ).resolve()

    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output = str(
        output_path
    )
    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output = str(
        summary_output_path
    )

    command = [
        sys.executable,
        str(
            REAL_LOOP_SUBMISSION_QUEUE_FOLLOWUP_RESOLUTION_ESCALATION_ACTION_PLAN_CLOSURE_CADENCE_ESCALATION_ACKNOWLEDGEMENT_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATION_CLOSURE_CADENCE_ESCALATIONS_SCRIPT
        ),
        "--submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-report",
        str(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
            ).resolve()
        ),
        "--output",
        str(output_path),
        "--summary-output",
        str(summary_output_path),
        "--owner",
        str(args.backfill_submission_owner).strip() or "controlled-beta-ops",
        "--escalate-after-due-hours",
        str(
            float(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalate_after_due_hours
            )
        ),
    ]
    now_utc = str(
        args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_now_utc
    ).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    return command

def _build_backfill_handoff_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(REAL_LOOP_BACKFILL_HANDOFF_SCRIPT),
        "--intake-actions-report",
        str(Path(args.backfill_intake_actions_output).resolve()),
        "--collection-report",
        str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
        "--output",
        str(Path(args.backfill_handoff_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_handoff_summary_output).resolve()),
        "--owner",
        str(args.backfill_handoff_owner).strip() or "controlled-beta-ops",
        "--pending-ack-sla-hours",
        str(float(args.backfill_handoff_pending_ack_sla_hours)),
        "--pending-ack-overdue-hours",
        str(float(args.backfill_handoff_pending_ack_overdue_hours)),
    ]
    now_utc = str(args.backfill_handoff_now_utc).strip()
    if now_utc:
        command.extend(["--now-utc", now_utc])
    ack_report = str(args.backfill_handoff_acknowledgements_report).strip()
    if ack_report:
        command.extend(["--acknowledgements-report", str(Path(ack_report).resolve())])
    return command


def _build_backfill_handoff_escalations_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(REAL_LOOP_BACKFILL_HANDOFF_ESCALATIONS_SCRIPT),
        "--handoff-report",
        str(Path(args.backfill_handoff_output).resolve()),
        "--output",
        str(Path(args.backfill_handoff_escalations_output).resolve()),
        "--summary-output",
        str(Path(args.backfill_handoff_escalations_summary_output).resolve()),
        "--owner",
        str(args.backfill_handoff_escalations_owner).strip() or "controlled-beta-ops",
    ]


def _build_launch_gate_command(
    args: argparse.Namespace,
    *,
    trial_metrics_report: Path,
    controlled_trial_run_report: Path,
    launch_readiness_output: Path,
) -> list[str]:
    command = [
        sys.executable,
        str(LAUNCH_READINESS_GATE_SCRIPT),
        "--release-switch-report",
        str(Path(args.release_switch_report).resolve()),
        "--current-status-doc",
        str(Path(args.current_status_doc).resolve()),
        "--trial-metrics-report",
        str(trial_metrics_report),
        "--controlled-trial-run-report",
        str(controlled_trial_run_report),
        "--agent-smoke-report",
        str(Path(args.agent_smoke_report).resolve()),
        "--doc-sync-report",
        str(Path(args.doc_sync_report).resolve()),
        "--operations-readiness-report",
        str(Path(args.operations_readiness_report).resolve()),
        "--minimum-complete-loops",
        str(max(1, int(args.minimum_complete_loops))),
        "--minimum-modalities",
        str(max(1, int(args.minimum_modalities))),
        "--max-evidence-age-hours",
        str(float(args.max_evidence_age_hours)),
        "--output",
        str(launch_readiness_output),
        "--summary-output",
        str(args.launch_readiness_summary_output),
    ]
    security_gate_report_value = str(args.security_gate_report).strip()
    if security_gate_report_value:
        command.extend(["--security-gate-report", str(Path(security_gate_report_value).resolve())])
    command.append("--run-doc-sync" if args.run_doc_sync else "--no-run-doc-sync")
    if args.print_json:
        command.append("--print-json")
    if args.print_summary:
        command.append("--print-summary")
    return command


def _read_submission_consumption_status(consumption_report_path: Path) -> tuple[str, int]:
    payload = _read_json(consumption_report_path)
    status = str(payload.get("consumption_status", "unknown")).strip()
    counts = payload.get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    consumed_loop_count = _to_int(counts.get("consumed_loop_count", 0), default=0)
    return status, consumed_loop_count


def _strip_windows_extended_path_prefix(path_text: str) -> str:
    if path_text.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path_text[8:]
    if path_text.startswith("\\\\?\\"):
        return path_text[4:]
    return path_text


def _format_evidence_path_text(value: str) -> str:
    text = str(value)
    if not text:
        return text
    cleaned = _strip_windows_extended_path_prefix(text)
    candidate = Path(cleaned)
    if candidate.is_absolute():
        try:
            relative = candidate.resolve().relative_to(REPO_ROOT)
        except ValueError:
            return cleaned
        return relative.as_posix()

    path_prefixes = (
        "apps/",
        "apps\\",
        "docs/",
        "docs\\",
        "scripts/",
        "scripts\\",
        "src/",
        "src\\",
        "tests/",
        "tests\\",
    )
    if cleaned.startswith(path_prefixes):
        return cleaned.replace("\\", "/")
    return text


def _normalize_evidence_pack_paths(value: Any) -> Any:
    if isinstance(value, dict):
        for key, item in list(value.items()):
            value[key] = _normalize_evidence_pack_paths(item)
        return value
    if isinstance(value, list):
        for index, item in enumerate(list(value)):
            value[index] = _normalize_evidence_pack_paths(item)
        return value
    if isinstance(value, str):
        return _format_evidence_path_text(value)
    return value


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        strings: list[str] = []
        for item in value.values():
            strings.extend(_walk_strings(item))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_walk_strings(item))
        return strings
    if isinstance(value, str):
        return [value]
    return []


def _is_repo_absolute_path_text(value: str) -> bool:
    cleaned = _strip_windows_extended_path_prefix(str(value))
    candidate = Path(cleaned)
    if not candidate.is_absolute():
        return False
    try:
        candidate.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return False
    return True


def _is_external_absolute_path_text(value: str) -> bool:
    cleaned = _strip_windows_extended_path_prefix(str(value))
    candidate = Path(cleaned)
    if not candidate.is_absolute():
        return False
    try:
        candidate.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return True
    return False


def _is_old_docs_current_path_text(value: str) -> bool:
    normalized = str(value).replace("\\", "/").lower()
    return "docs/current/" in normalized or normalized.endswith("docs/current")


def _build_path_hygiene(evidence_pack: dict[str, Any]) -> dict[str, Any]:
    values = _walk_strings(evidence_pack)
    old_docs_current_paths = sorted({value for value in values if _is_old_docs_current_path_text(value)})
    repo_root_absolute_paths = sorted({value for value in values if _is_repo_absolute_path_text(value)})
    external_absolute_paths = sorted({value for value in values if _is_external_absolute_path_text(value)})
    return {
        "schema_version": "real_trial_launch_evidence_path_hygiene.v1",
        "old_docs_current_path_count": len(old_docs_current_paths),
        "old_docs_current_paths": old_docs_current_paths,
        "repo_root_absolute_path_count": len(repo_root_absolute_paths),
        "repo_root_absolute_paths": repo_root_absolute_paths,
        "external_absolute_path_count": len(external_absolute_paths),
        "external_absolute_paths": external_absolute_paths,
    }


def _success_condition_by_id(trial_metrics_report: dict[str, Any], condition_id: str) -> dict[str, Any]:
    success_criteria = trial_metrics_report.get("success_criteria", {})
    if not isinstance(success_criteria, dict):
        return {}
    conditions = success_criteria.get("conditions", [])
    if not isinstance(conditions, list):
        return {}
    for condition in conditions:
        if not isinstance(condition, dict):
            continue
        if str(condition.get("id", "")).strip() == condition_id:
            return condition
    return {}


def _success_condition_status(condition: dict[str, Any]) -> str:
    return str(condition.get("status", "unknown")).strip() or "unknown"


def _build_evidence_pack(
    *,
    args: argparse.Namespace,
    collection_report: dict[str, Any],
    trial_metrics_report: dict[str, Any],
    launch_readiness_report: dict[str, Any],
    backfill_execution_report: dict[str, Any],
    backfill_intake_actions_report: dict[str, Any],
    backfill_submission_templates_report: dict[str, Any],
    backfill_submission_consumption_report: dict[str, Any],
    backfill_submission_throughput_report: dict[str, Any],
    backfill_submission_queue_report: dict[str, Any],
    backfill_submission_queue_completion_report: dict[str, Any],
    backfill_submission_queue_commitments_report: dict[str, Any],
    backfill_submission_queue_commitment_closure_report: dict[str, Any],
    backfill_submission_queue_followup_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalations_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_acknowledgements_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_throughput_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report: dict[str, Any],
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report: dict[str, Any],
    backfill_handoff_report: dict[str, Any],
    backfill_handoff_escalations_report: dict[str, Any],
    manifest_preflight_report: dict[str, Any],
    run_report_paths: list[Path],
    loop_manifest_paths: list[Path],
) -> dict[str, Any]:
    trial_metrics = trial_metrics_report.get("trial_metrics", {})
    if not isinstance(trial_metrics, dict):
        trial_metrics = {}
    launch_gate_evidence = trial_metrics.get("launch_gate_evidence", {})
    if not isinstance(launch_gate_evidence, dict):
        launch_gate_evidence = {}
    review_quality = trial_metrics.get("review_quality", {})
    if not isinstance(review_quality, dict):
        review_quality = {}
    reviewer_edit_distance = trial_metrics.get("reviewer_edit_distance_pct", {})
    if not isinstance(reviewer_edit_distance, dict):
        reviewer_edit_distance = {}
    provider_runtime = trial_metrics.get("provider_runtime", {})
    if not isinstance(provider_runtime, dict):
        provider_runtime = {}
    cost_placeholder = trial_metrics.get("cost_placeholder", {})
    if not isinstance(cost_placeholder, dict):
        cost_placeholder = {}
    success_criteria = trial_metrics_report.get("success_criteria", {})
    if not isinstance(success_criteria, dict):
        success_criteria = {}
    reviewer_approval_condition = _success_condition_by_id(trial_metrics_report, "reviewer_approval_rate")
    median_reviewer_edit_distance_condition = _success_condition_by_id(
        trial_metrics_report,
        "median_reviewer_edit_distance",
    )
    agent_smoke_success_condition = _success_condition_by_id(trial_metrics_report, "agent_smoke_success_rate")
    provider_failure_condition = _success_condition_by_id(trial_metrics_report, "provider_failure_rate")
    cost_per_accepted_skill_condition = _success_condition_by_id(trial_metrics_report, "cost_per_accepted_skill")
    safety = trial_metrics.get("safety", {})
    if not isinstance(safety, dict):
        safety = {}
    collection_alignment = collection_report.get("launch_gate_alignment", {})
    if not isinstance(collection_alignment, dict):
        collection_alignment = {}
    backfill_slot_counts = backfill_execution_report.get("slot_counts", {})
    if not isinstance(backfill_slot_counts, dict):
        backfill_slot_counts = {}
    backfill_submission_backed_slot_counts = backfill_execution_report.get("submission_backed_slot_counts", {})
    if not isinstance(backfill_submission_backed_slot_counts, dict):
        backfill_submission_backed_slot_counts = {}
    backfill_submission_linkage_counts = backfill_execution_report.get("submission_linkage_counts", {})
    if not isinstance(backfill_submission_linkage_counts, dict):
        backfill_submission_linkage_counts = {}
    backfill_coverage_delta = backfill_execution_report.get("coverage_delta", {})
    if not isinstance(backfill_coverage_delta, dict):
        backfill_coverage_delta = {}
    backfill_intake_action_counts = backfill_intake_actions_report.get("action_counts", {})
    if not isinstance(backfill_intake_action_counts, dict):
        backfill_intake_action_counts = {}
    backfill_submission_template_counts = backfill_submission_templates_report.get("template_counts", {})
    if not isinstance(backfill_submission_template_counts, dict):
        backfill_submission_template_counts = {}
    backfill_submission_action_counts = backfill_submission_templates_report.get("action_counts", {})
    if not isinstance(backfill_submission_action_counts, dict):
        backfill_submission_action_counts = {}
    backfill_submission_consumption_counts = backfill_submission_consumption_report.get("counts", {})
    if not isinstance(backfill_submission_consumption_counts, dict):
        backfill_submission_consumption_counts = {}
    backfill_submission_throughput_snapshot = backfill_submission_throughput_report.get("snapshot", {})
    if not isinstance(backfill_submission_throughput_snapshot, dict):
        backfill_submission_throughput_snapshot = {}
    backfill_submission_throughput_current = backfill_submission_throughput_snapshot.get("current", {})
    if not isinstance(backfill_submission_throughput_current, dict):
        backfill_submission_throughput_current = {}
    backfill_submission_throughput_delta = backfill_submission_throughput_snapshot.get("delta", {})
    if not isinstance(backfill_submission_throughput_delta, dict):
        backfill_submission_throughput_delta = {}
    backfill_submission_execution_focus = backfill_submission_throughput_report.get("execution_focus", {})
    if not isinstance(backfill_submission_execution_focus, dict):
        backfill_submission_execution_focus = {}
    backfill_submission_queue_summary = backfill_submission_queue_report.get("queue_summary", {})
    if not isinstance(backfill_submission_queue_summary, dict):
        backfill_submission_queue_summary = {}
    backfill_submission_queue_refresh_cadence = backfill_submission_queue_report.get("refresh_cadence", {})
    if not isinstance(backfill_submission_queue_refresh_cadence, dict):
        backfill_submission_queue_refresh_cadence = {}
    backfill_submission_queue_completion_counts = backfill_submission_queue_completion_report.get(
        "queue_completion_counts", {}
    )
    if not isinstance(backfill_submission_queue_completion_counts, dict):
        backfill_submission_queue_completion_counts = {}
    backfill_submission_queue_cycle_verification = backfill_submission_queue_completion_report.get(
        "cycle_movement_verification", {}
    )
    if not isinstance(backfill_submission_queue_cycle_verification, dict):
        backfill_submission_queue_cycle_verification = {}
    backfill_submission_queue_commitment_counts = backfill_submission_queue_commitments_report.get(
        "commitment_counts", {}
    )
    if not isinstance(backfill_submission_queue_commitment_counts, dict):
        backfill_submission_queue_commitment_counts = {}
    backfill_submission_queue_commitment_cycle_snapshot = backfill_submission_queue_commitments_report.get(
        "cycle_snapshot", {}
    )
    if not isinstance(backfill_submission_queue_commitment_cycle_snapshot, dict):
        backfill_submission_queue_commitment_cycle_snapshot = {}
    backfill_submission_queue_commitment_closure_counts = backfill_submission_queue_commitment_closure_report.get(
        "closure_counts", {}
    )
    if not isinstance(backfill_submission_queue_commitment_closure_counts, dict):
        backfill_submission_queue_commitment_closure_counts = {}
    backfill_submission_queue_followup_counts = backfill_submission_queue_followup_report.get(
        "followup_counts", {}
    )
    if not isinstance(backfill_submission_queue_followup_counts, dict):
        backfill_submission_queue_followup_counts = {}
    backfill_submission_queue_followup_resolution_counts = (
        backfill_submission_queue_followup_resolution_report.get("followup_resolution_counts", {})
    )
    if not isinstance(backfill_submission_queue_followup_resolution_counts, dict):
        backfill_submission_queue_followup_resolution_counts = {}
    backfill_submission_queue_followup_resolution_escalations_counts = (
        backfill_submission_queue_followup_resolution_escalations_report.get(
            "followup_resolution_escalation_counts",
            {},
        )
    )
    if not isinstance(backfill_submission_queue_followup_resolution_escalations_counts, dict):
        backfill_submission_queue_followup_resolution_escalations_counts = {}
    backfill_submission_queue_followup_resolution_escalation_acknowledgements_counts = (
        backfill_submission_queue_followup_resolution_escalation_acknowledgements_report.get(
            "followup_resolution_escalation_acknowledgement_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_acknowledgements_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_acknowledgements_counts = {}
    backfill_submission_queue_followup_resolution_escalation_throughput_delta = (
        backfill_submission_queue_followup_resolution_escalation_throughput_report.get(
            "snapshot_delta",
            {},
        )
    )
    if not isinstance(backfill_submission_queue_followup_resolution_escalation_throughput_delta, dict):
        backfill_submission_queue_followup_resolution_escalation_throughput_delta = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_report.get(
            "followup_resolution_escalation_action_plan_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report.get(
            "followup_resolution_escalation_action_plan_closure_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_delta = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report.get(
            "snapshot_delta",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_delta,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_delta = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report.get(
            "refresh_cadence",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report.get(
            "acknowledgement_input_snapshot",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report.get(
            "refresh_cadence",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report.get(
            "refresh_cadence",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
            "refresh_cadence",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
            "refresh_cadence",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh = {}
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts = (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
            "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_counts",
            {},
        )
    )
    if not isinstance(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts,
        dict,
    ):
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts = {}
    backfill_handoff_counts = backfill_handoff_report.get("queue_item_counts", {})
    if not isinstance(backfill_handoff_counts, dict):
        backfill_handoff_counts = {}
    backfill_handoff_submission_linkage_snapshot = backfill_handoff_report.get("submission_linkage_snapshot", {})
    if not isinstance(backfill_handoff_submission_linkage_snapshot, dict):
        backfill_handoff_submission_linkage_snapshot = {}
    backfill_handoff_ack_snapshot = backfill_handoff_report.get("acknowledgement_snapshot", {})
    if not isinstance(backfill_handoff_ack_snapshot, dict):
        backfill_handoff_ack_snapshot = {}
    backfill_handoff_ack_sla_snapshot = backfill_handoff_report.get("acknowledgement_sla_snapshot", {})
    if not isinstance(backfill_handoff_ack_sla_snapshot, dict):
        backfill_handoff_ack_sla_snapshot = {}
    backfill_handoff_escalation_counts = backfill_handoff_escalations_report.get("escalation_counts", {})
    if not isinstance(backfill_handoff_escalation_counts, dict):
        backfill_handoff_escalation_counts = {}
    backfill_handoff_escalation_exports = backfill_handoff_escalations_report.get("escalation_exports", {})
    if not isinstance(backfill_handoff_escalation_exports, dict):
        backfill_handoff_escalation_exports = {}
    manifest_preflight_counts = manifest_preflight_report.get("counts", {})
    if not isinstance(manifest_preflight_counts, dict):
        manifest_preflight_counts = {}
    manifest_preflight_slot_readiness = manifest_preflight_report.get("slot_readiness", {})
    if not isinstance(manifest_preflight_slot_readiness, dict):
        manifest_preflight_slot_readiness = {}
    manifest_preflight_modality_readiness = manifest_preflight_report.get("modality_readiness", {})
    if not isinstance(manifest_preflight_modality_readiness, dict):
        manifest_preflight_modality_readiness = {}
    manifest_preflight_operator_action_plan = manifest_preflight_report.get("operator_action_plan", {})
    if not isinstance(manifest_preflight_operator_action_plan, dict):
        manifest_preflight_operator_action_plan = {}
    failed_checks = launch_readiness_report.get("failed_checks", [])
    if not isinstance(failed_checks, list):
        failed_checks = []
    decision = str(launch_readiness_report.get("decision", "HOLD")).strip().upper() or "HOLD"

    evidence_pack = {
        "schema_version": "real_trial_launch_evidence_pack.v1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "stage": "controlled_external_beta",
        "launch_decision": decision,
        "ready_for_controlled_beta": decision == "READY_FOR_CONTROLLED_BETA",
        "ready_for_ga_review": decision == "READY_FOR_GA_REVIEW",
        "ready_for_platform_beta": decision == "READY_FOR_PLATFORM_BETA",
        "evidence_paths": {
            "collection_report": str(_resolve_required_output_path(args.collection_report_output, name="collection-report-output")),
            "collection_summary": str(Path(args.collection_summary_output).resolve()),
            "real_trial_manifest": str(_resolve_required_output_path(args.real_trial_manifest_output, name="real-trial-manifest-output")),
            "real_trial_backfill_plan": str(Path(args.backfill_plan_output).resolve()),
            "real_trial_backfill_execution_report": str(Path(args.backfill_execution_output).resolve()),
            "real_trial_backfill_execution_summary": str(Path(args.backfill_execution_summary_output).resolve()),
            "real_trial_backfill_intake_actions_report": str(Path(args.backfill_intake_actions_output).resolve()),
            "real_trial_backfill_intake_actions_summary": str(Path(args.backfill_intake_actions_summary_output).resolve()),
            "real_trial_backfill_submission_templates_report": str(
                Path(args.backfill_submission_templates_output).resolve()
            ),
            "real_trial_backfill_submission_templates_summary": str(
                Path(args.backfill_submission_templates_summary_output).resolve()
            ),
            "real_trial_backfill_submission_manifest_template": str(
                Path(args.backfill_submission_manifest_template_output).resolve()
            ),
            "real_trial_backfill_submission_real_inputs": str(
                Path(args.backfill_submission_real_inputs).resolve()
            ),
            "real_trial_backfill_submission_consumption_report": str(
                Path(args.backfill_submission_consumption_output).resolve()
            ),
            "real_trial_backfill_submission_consumption_summary": str(
                Path(args.backfill_submission_consumption_summary_output).resolve()
            ),
            "real_trial_backfill_submission_consumed_manifest": str(
                Path(args.backfill_submission_consumed_manifest_output).resolve()
            ),
            "real_trial_backfill_submission_throughput_report": str(
                Path(args.backfill_submission_throughput_output).resolve()
            ),
            "real_trial_backfill_submission_throughput_summary": str(
                Path(args.backfill_submission_throughput_summary_output).resolve()
            ),
            "real_trial_backfill_submission_queue_report": str(
                Path(args.backfill_submission_queue_output).resolve()
            ),
            "real_trial_backfill_submission_queue_summary": str(
                Path(args.backfill_submission_queue_summary_output).resolve()
            ),
            "real_trial_backfill_submission_queue_completion_report": str(
                Path(args.backfill_submission_queue_completion_output).resolve()
            ),
            "real_trial_backfill_submission_queue_completion_summary": str(
                Path(args.backfill_submission_queue_completion_summary_output).resolve()
            ),
            "real_trial_backfill_submission_queue_commitments_report": str(
                Path(args.backfill_submission_queue_commitments_output).resolve()
            ),
            "real_trial_backfill_submission_queue_commitments_summary": str(
                Path(args.backfill_submission_queue_commitments_summary_output).resolve()
            ),
            "real_trial_backfill_submission_queue_commitment_closure_report": str(
                Path(args.backfill_submission_queue_commitment_closure_output).resolve()
            ),
            "real_trial_backfill_submission_queue_commitment_closure_summary": str(
                Path(args.backfill_submission_queue_commitment_closure_summary_output).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_report": str(
                Path(args.backfill_submission_queue_followup_output).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_summary": str(
                Path(args.backfill_submission_queue_followup_summary_output).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_report": str(
                Path(args.backfill_submission_queue_followup_resolution_output).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_summary": str(
                Path(args.backfill_submission_queue_followup_resolution_summary_output).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalations_report": str(
                Path(args.backfill_submission_queue_followup_resolution_escalations_output).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalations_summary": str(
                Path(args.backfill_submission_queue_followup_resolution_escalations_summary_output).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_acknowledgements_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_acknowledgements_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_throughput_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_throughput_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_throughput_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_throughput_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_summary_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output
                ).resolve()
            ),
            "real_trial_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary": str(
                Path(
                    args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_summary_output
                ).resolve()
            ),
            "real_trial_backfill_handoff_report": str(Path(args.backfill_handoff_output).resolve()),
            "real_trial_backfill_handoff_summary": str(Path(args.backfill_handoff_summary_output).resolve()),
            "real_trial_backfill_handoff_acknowledgements_report": str(
                Path(args.backfill_handoff_acknowledgements_report).resolve()
            )
            if str(args.backfill_handoff_acknowledgements_report).strip()
            else "",
            "real_trial_backfill_handoff_escalations_report": str(
                Path(args.backfill_handoff_escalations_output).resolve()
            ),
            "real_trial_backfill_handoff_escalations_summary": str(
                Path(args.backfill_handoff_escalations_summary_output).resolve()
            ),
            "real_trial_loop_manifest_preflight_report": str(Path(args.manifest_preflight_report).resolve()),
            "real_trial_loop_manifest_preflight_summary": str(Path(args.manifest_preflight_summary).resolve()),
            "trial_metrics_report": str(_resolve_required_output_path(args.trial_metrics_report_output, name="trial-metrics-report-output")),
            "trial_metrics_summary": str(Path(args.trial_metrics_summary_output).resolve()),
            "launch_readiness_report": str(_resolve_required_output_path(args.launch_readiness_output, name="launch-readiness-output")),
            "launch_readiness_summary": str(Path(args.launch_readiness_summary_output).resolve()),
        },
        "input_sources": {
            "run_report_paths": [str(path) for path in run_report_paths],
            "loop_manifest_paths": collection_report.get("source_loop_manifest_paths", []),
            "input_report_count": len(run_report_paths),
            "input_loop_manifest_count": int(collection_report.get("input_loop_manifest_count", 0) or 0),
            "ingested_loop_manifest_count": int(collection_report.get("ingested_loop_manifest_count", 0) or 0),
            "skipped_non_loop_manifest_count": int(
                collection_report.get("skipped_non_loop_manifest_count", 0) or 0
            ),
            "skipped_non_loop_manifest_paths": collection_report.get("skipped_non_loop_manifest_paths", []),
            "input_loop_manifest_dir_count": int(collection_report.get("input_loop_manifest_dir_count", 0) or 0),
            "loop_manifest_dirs": collection_report.get("source_loop_manifest_dirs", []),
            "duplicate_resolution_count": int(collection_report.get("duplicate_resolution_count", 0) or 0),
            "duplicate_resolution_records": collection_report.get("duplicate_resolution_records", []),
            "backfill_submission_ingestion_replay_applied": bool(
                getattr(args, "backfill_submission_ingestion_replay_applied", False)
            ),
            "backfill_submission_ingestion_replay_manifest_paths": list(
                getattr(args, "backfill_submission_ingestion_replay_manifest_paths", [])
            ),
            "backfill_submission_ingestion_consumed_loop_count": int(
                getattr(args, "backfill_submission_ingestion_consumed_loop_count", 0) or 0
            ),
            "backfill_submission_ingestion_status": str(
                getattr(args, "backfill_submission_ingestion_status", "unknown")
            ),
        },
        "evidence_classification": {
            "evidence_origin_counts": collection_report.get("evidence_origin_counts", {}),
            "launch_gate_ineligible_reason_counts": collection_report.get("launch_gate_ineligible_reason_counts", {}),
            "total_complete_loop_count": int(trial_metrics.get("complete_loop_count", 0) or 0),
            "total_complete_modalities": trial_metrics.get("complete_modalities", []),
            "launch_gate_eligible_complete_loop_count": int(launch_gate_evidence.get("complete_loop_count", 0) or 0),
            "launch_gate_eligible_complete_modalities": launch_gate_evidence.get("complete_modalities", []),
            "target_launch_modalities": collection_alignment.get("target_launch_modalities", []),
            "covered_target_launch_modalities": collection_alignment.get("covered_target_launch_modalities", []),
            "missing_target_launch_modalities": collection_alignment.get("missing_target_launch_modalities", []),
            "recommended_next_modalities": collection_alignment.get("recommended_next_modalities", []),
            "real_loop_manifest_preflight_status": str(manifest_preflight_report.get("status", "unknown")),
            "real_loop_manifest_preflight_launch_gate_policy_unchanged": bool(
                manifest_preflight_report.get("launch_gate_policy_unchanged", False)
            ),
            "real_loop_manifest_preflight_warning_codes": manifest_preflight_report.get("warning_codes", []),
            "real_loop_manifest_preflight_total_intake_item_count": int(
                manifest_preflight_counts.get("total_intake_item_count", 0) or 0
            ),
            "real_loop_manifest_preflight_submitted_manifest_count": int(
                manifest_preflight_counts.get("submitted_manifest_count", 0) or 0
            ),
            "real_loop_manifest_preflight_valid_item_count": int(
                manifest_preflight_counts.get("valid_item_count", 0) or 0
            ),
            "real_loop_manifest_preflight_missing_item_count": int(
                manifest_preflight_counts.get("missing_item_count", 0) or 0
            ),
            "real_loop_manifest_preflight_invalid_item_count": int(
                manifest_preflight_counts.get("invalid_item_count", 0) or 0
            ),
            "real_loop_manifest_preflight_accepted_loop_count": int(
                manifest_preflight_counts.get("accepted_loop_count", 0) or 0
            ),
            "real_loop_manifest_preflight_required_slot_count": int(
                manifest_preflight_slot_readiness.get("required_slot_count", 0) or 0
            ),
            "real_loop_manifest_preflight_ready_slot_count": int(
                manifest_preflight_slot_readiness.get("ready_slot_count", 0) or 0
            ),
            "real_loop_manifest_preflight_blocked_slot_count": int(
                manifest_preflight_slot_readiness.get("blocked_slot_count", 0) or 0
            ),
            "real_loop_manifest_preflight_missing_slot_count": int(
                manifest_preflight_slot_readiness.get("missing_slot_count", 0) or 0
            ),
            "real_loop_manifest_preflight_invalid_slot_count": int(
                manifest_preflight_slot_readiness.get("invalid_slot_count", 0) or 0
            ),
            "real_loop_manifest_preflight_missing_manifest_paths": manifest_preflight_slot_readiness.get(
                "missing_manifest_paths",
                [],
            ),
            "real_loop_manifest_preflight_invalid_manifest_paths": manifest_preflight_slot_readiness.get(
                "invalid_manifest_paths",
                [],
            ),
            "real_loop_manifest_preflight_first_blocking_slot": manifest_preflight_slot_readiness.get(
                "first_blocking_slot",
                None,
            ),
            "real_loop_manifest_preflight_target_launch_modalities": manifest_preflight_modality_readiness.get(
                "target_launch_modalities",
                [],
            ),
            "real_loop_manifest_preflight_covered_target_launch_modalities": manifest_preflight_modality_readiness.get(
                "covered_target_launch_modalities",
                [],
            ),
            "real_loop_manifest_preflight_missing_target_launch_modalities": manifest_preflight_modality_readiness.get(
                "missing_target_launch_modalities",
                [],
            ),
            "real_loop_manifest_preflight_operator_action_status": str(
                manifest_preflight_operator_action_plan.get("status", "unknown")
            ),
            "real_loop_manifest_preflight_operator_pending_action_count": int(
                manifest_preflight_operator_action_plan.get("pending_action_count", 0) or 0
            ),
            "real_loop_manifest_preflight_operator_next_actions": manifest_preflight_operator_action_plan.get(
                "next_actions",
                [],
            ),
            "launch_gate_eligible_complete_loop_count_by_modality": collection_alignment.get(
                "launch_gate_eligible_complete_loop_count_by_modality", {}
            ),
            "target_launch_modality_loop_counts": collection_alignment.get("target_launch_modality_loop_counts", {}),
            "real_evidence_missing_source_trace_count": int(
                launch_gate_evidence.get("real_evidence_missing_source_trace_count", 0) or 0
            ),
            "real_evidence_missing_review_trace_count": int(
                launch_gate_evidence.get("real_evidence_missing_review_trace_count", 0) or 0
            ),
            "real_evidence_template_placeholder_loop_count": int(
                launch_gate_evidence.get("real_evidence_template_placeholder_loop_count", 0) or 0
            ),
            "real_evidence_template_placeholder_field_count": int(
                launch_gate_evidence.get("real_evidence_template_placeholder_field_count", 0) or 0
            ),
            "real_evidence_template_placeholder_records": launch_gate_evidence.get(
                "real_evidence_template_placeholder_records",
                [],
            ),
            "trial_success_criteria_status": str(success_criteria.get("status", "unknown")),
            "trial_success_criteria_passed_count": int(success_criteria.get("passed_count", 0) or 0),
            "trial_success_criteria_failed_count": int(success_criteria.get("failed_count", 0) or 0),
            "trial_success_criteria_failed_condition_ids": [
                str(item.get("id", "")).strip()
                for item in success_criteria.get("failed_conditions", [])
                if isinstance(item, dict) and str(item.get("id", "")).strip()
            ]
            if isinstance(success_criteria.get("failed_conditions", []), list)
            else [],
            "trial_quality_reviewer_approval_rate_status": _success_condition_status(
                reviewer_approval_condition
            ),
            "trial_quality_reviewer_approval_rate": _to_float(
                review_quality.get("approval_rate_after_one_revision", 0.0),
            ),
            "trial_quality_reviewer_approval_rate_expected_min": _to_float(
                reviewer_approval_condition.get("expected_min", 0.0),
            ),
            "trial_quality_review_evaluable_count": int(review_quality.get("review_evaluable_count", 0) or 0),
            "trial_quality_approved_after_one_revision_count": int(
                review_quality.get("approved_after_one_revision_count", 0) or 0
            ),
            "trial_quality_median_reviewer_edit_distance_status": _success_condition_status(
                median_reviewer_edit_distance_condition
            ),
            "trial_quality_median_reviewer_edit_distance_pct": _to_float(
                reviewer_edit_distance.get("median", 0.0),
            ),
            "trial_quality_median_reviewer_edit_distance_expected_max": _to_float(
                median_reviewer_edit_distance_condition.get("expected_max", 0.0),
            ),
            "trial_quality_reviewer_edit_distance_sample_count": int(
                reviewer_edit_distance.get("samples", 0) or 0
            ),
            "trial_quality_agent_smoke_success_rate_status": _success_condition_status(
                agent_smoke_success_condition
            ),
            "trial_quality_agent_smoke_success_rate": _to_float(
                review_quality.get("agent_smoke_success_rate", 0.0),
            ),
            "trial_quality_agent_smoke_success_rate_expected_min": _to_float(
                agent_smoke_success_condition.get("expected_min", 0.0),
            ),
            "trial_quality_approved_with_not_run_smoke_count": int(
                review_quality.get("approved_with_not_run_smoke_count", 0) or 0
            ),
            "trial_quality_provider_failure_rate_status": _success_condition_status(
                provider_failure_condition
            ),
            "trial_quality_provider_failure_rate": _to_float(
                provider_runtime.get("provider_failure_rate", 0.0),
            ),
            "trial_quality_provider_failure_rate_expected_max": _to_float(
                provider_failure_condition.get("expected_max", 0.0),
            ),
            "trial_quality_provider_failure_count_total": int(
                provider_runtime.get("provider_failure_count_total", 0) or 0
            ),
            "trial_quality_provider_call_count_total": int(
                provider_runtime.get("provider_call_count_total", 0) or 0
            ),
            "trial_quality_retry_count_total": int(provider_runtime.get("retry_count_total", 0) or 0),
            "trial_quality_cost_per_accepted_skill_status": _success_condition_status(
                cost_per_accepted_skill_condition
            ),
            "trial_quality_cost_per_accepted_skill_usd": _to_float(
                cost_placeholder.get("cost_per_accepted_skill_usd", 0.0),
            ),
            "trial_quality_cost_approved_skill_count": int(
                cost_placeholder.get("approved_skill_count", 0) or 0
            ),
            "trial_quality_cost_missing_count": int(
                cost_placeholder.get("approved_skill_missing_cost_count", 0) or 0
            ),
            "trial_quality_cost_accepted_by_operator": bool(
                cost_placeholder.get("accepted_by_operator", False)
            ),
            "collection_program_status": str(collection_alignment.get("program_status", "unknown")),
            "collection_blockers": collection_alignment.get("blockers", []),
            "missing_complete_loops_to_threshold": int(
                collection_alignment.get("missing_complete_loops_to_threshold", 0) or 0
            ),
            "missing_modalities_to_threshold": int(
                collection_alignment.get("missing_modalities_to_threshold", 0) or 0
            ),
            "recommended_backfill_slot_count": int(collection_alignment.get("recommended_backfill_slot_count", 0) or 0),
            "recommended_backfill_slots": collection_alignment.get("recommended_backfill_slots", []),
            "backfill_execution_status": str(backfill_execution_report.get("execution_status", "unknown")),
            "backfill_execution_fulfilled_slot_count": int(backfill_slot_counts.get("fulfilled_slot_count", 0) or 0),
            "backfill_execution_remaining_slot_count": int(backfill_slot_counts.get("remaining_slot_count", 0) or 0),
            "backfill_execution_submission_backed_status": str(
                backfill_execution_report.get("submission_backed_execution_status", "unknown")
            ),
            "backfill_execution_submission_backed_fulfilled_slot_count": int(
                backfill_submission_backed_slot_counts.get("submission_backed_fulfilled_slot_count", 0) or 0
            ),
            "backfill_execution_submission_backed_remaining_slot_count": int(
                backfill_submission_backed_slot_counts.get("submission_backed_remaining_slot_count", 0) or 0
            ),
            "backfill_execution_fulfilled_without_submission_linkage_count": int(
                backfill_submission_backed_slot_counts.get("fulfilled_without_submission_linkage_count", 0) or 0
            ),
            "backfill_execution_submission_linked_without_modality_delta_count": int(
                backfill_submission_backed_slot_counts.get("submission_linked_without_modality_delta_count", 0) or 0
            ),
            "backfill_execution_gained_target_launch_modality_loop_counts": backfill_coverage_delta.get(
                "gained_target_launch_modality_loop_counts",
                {},
            ),
            "backfill_execution_submission_linked_slot_count": int(
                backfill_submission_linkage_counts.get("submission_linked_slot_count", 0) or 0
            ),
            "backfill_execution_submission_slot_linked_count": int(
                backfill_submission_linkage_counts.get("slot_linked_count", 0) or 0
            ),
            "backfill_execution_submission_action_linked_count": int(
                backfill_submission_linkage_counts.get("action_linked_count", 0) or 0
            ),
            "backfill_execution_unmatched_submission_linkage_count": int(
                backfill_submission_linkage_counts.get("unmatched_submission_linkage_count", 0) or 0
            ),
            "backfill_execution_submission_linkage_records": backfill_execution_report.get(
                "submission_linkage_records",
                [],
            ),
            "backfill_execution_unmatched_submission_linkages": backfill_execution_report.get(
                "unmatched_submission_linkages",
                [],
            ),
            "backfill_intake_status": str(backfill_intake_actions_report.get("intake_status", "unknown")),
            "backfill_intake_total_action_count": int(backfill_intake_action_counts.get("total_actions", 0) or 0),
            "backfill_intake_pending_action_count": int(backfill_intake_action_counts.get("pending_action_count", 0) or 0),
            "backfill_intake_closed_action_count": int(backfill_intake_action_counts.get("closed_action_count", 0) or 0),
            "backfill_intake_owner": str(args.backfill_intake_owner).strip() or "controlled-beta-ops",
            "backfill_submission_template_status": str(
                backfill_submission_templates_report.get("template_status", "unknown")
            ),
            "backfill_submission_template_total_action_count": int(
                backfill_submission_action_counts.get("total_action_count", 0) or 0
            ),
            "backfill_submission_template_pending_action_count": int(
                backfill_submission_action_counts.get("pending_action_count", 0) or 0
            ),
            "backfill_submission_template_generated_count": int(
                backfill_submission_template_counts.get("generated_template_count", 0) or 0
            ),
            "backfill_submission_template_missing_count": int(
                backfill_submission_template_counts.get("missing_template_action_count", 0) or 0
            ),
            "backfill_submission_template_owner": str(args.backfill_submission_owner).strip()
            or "controlled-beta-ops",
            "backfill_submission_template_missing_actions": backfill_submission_templates_report.get(
                "missing_template_actions",
                [],
            ),
            "backfill_submission_consumption_status": str(
                backfill_submission_consumption_report.get("consumption_status", "unknown")
            ),
            "backfill_submission_consumption_template_loop_count": int(
                backfill_submission_consumption_counts.get("template_loop_count", 0) or 0
            ),
            "backfill_submission_consumption_submitted_row_count": int(
                backfill_submission_consumption_counts.get("submitted_row_count", 0) or 0
            ),
            "backfill_submission_consumption_consumed_loop_count": int(
                backfill_submission_consumption_counts.get("consumed_loop_count", 0) or 0
            ),
            "backfill_submission_consumption_pending_template_loop_count": int(
                backfill_submission_consumption_counts.get("pending_template_loop_count", 0) or 0
            ),
            "backfill_submission_consumption_invalid_submission_count": int(
                backfill_submission_consumption_counts.get("invalid_submission_count", 0) or 0
            ),
            "backfill_submission_consumption_unresolved_submission_count": int(
                backfill_submission_consumption_counts.get("unresolved_submission_count", 0) or 0
            ),
            "backfill_submission_consumption_pending_template_rows": backfill_submission_consumption_report.get(
                "pending_template_rows",
                [],
            ),
            "backfill_submission_consumption_invalid_submissions": backfill_submission_consumption_report.get(
                "invalid_submissions",
                [],
            ),
            "backfill_submission_consumption_unresolved_submissions": backfill_submission_consumption_report.get(
                "unresolved_submissions",
                [],
            ),
            "backfill_submission_throughput_status": str(
                backfill_submission_throughput_report.get("throughput_status", "unknown")
            ),
            "backfill_submission_throughput_threshold_met": bool(
                backfill_submission_throughput_report.get("threshold_met", False)
            ),
            "backfill_submission_throughput_warning_codes": backfill_submission_throughput_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_throughput_previous_snapshot_available": bool(
                backfill_submission_throughput_snapshot.get("previous_snapshot_available", False)
            ),
            "backfill_submission_throughput_net_new_loop_count": int(
                backfill_submission_throughput_delta.get("net_new_launch_gate_eligible_real_loop_count", 0) or 0
            ),
            "backfill_submission_throughput_dropped_loop_count": int(
                backfill_submission_throughput_delta.get("dropped_launch_gate_eligible_real_loop_count", 0) or 0
            ),
            "backfill_submission_throughput_net_new_loop_ids": backfill_submission_throughput_snapshot.get(
                "net_new_launch_gate_eligible_real_loop_ids",
                [],
            ),
            "backfill_submission_throughput_dropped_loop_ids": backfill_submission_throughput_snapshot.get(
                "dropped_launch_gate_eligible_real_loop_ids",
                [],
            ),
            "backfill_submission_throughput_current_missing_loops_to_threshold": int(
                backfill_submission_throughput_current.get("missing_complete_loops_to_threshold", 0) or 0
            ),
            "backfill_submission_throughput_current_missing_modalities_to_threshold": int(
                backfill_submission_throughput_current.get("missing_modalities_to_threshold", 0) or 0
            ),
            "backfill_submission_throughput_current_remaining_slot_count": int(
                backfill_submission_throughput_current.get("backfill_execution_remaining_slot_count", 0) or 0
            ),
            "backfill_submission_throughput_current_submission_backed_remaining_slot_count": int(
                backfill_submission_throughput_current.get(
                    "backfill_execution_submission_backed_remaining_slot_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_throughput_action_plan_status": str(
                backfill_submission_execution_focus.get("action_plan_status", "unknown")
            ),
            "backfill_submission_throughput_action_plan_blockers": backfill_submission_execution_focus.get(
                "action_plan_blockers",
                [],
            ),
            "backfill_submission_throughput_pending_submission_action_count": int(
                backfill_submission_execution_focus.get("pending_submission_action_count", 0) or 0
            ),
            "backfill_submission_throughput_recommended_submission_action_count": int(
                backfill_submission_execution_focus.get("recommended_submission_action_count", 0) or 0
            ),
            "backfill_submission_throughput_priority_modalities": backfill_submission_execution_focus.get(
                "priority_modalities",
                [],
            ),
            "backfill_submission_throughput_recommended_submission_actions": backfill_submission_execution_focus.get(
                "recommended_submission_actions",
                [],
            ),
            "backfill_submission_throughput_submission_consumption_status": str(
                backfill_submission_execution_focus.get("submission_consumption_status", "unknown")
            ),
            "backfill_submission_throughput_submission_template_loop_count": int(
                backfill_submission_execution_focus.get("submission_consumption_template_loop_count", 0) or 0
            ),
            "backfill_submission_throughput_submission_pending_template_loop_count": int(
                backfill_submission_execution_focus.get("submission_consumption_pending_template_loop_count", 0) or 0
            ),
            "backfill_submission_throughput_submission_invalid_count": int(
                backfill_submission_execution_focus.get("submission_consumption_invalid_submission_count", 0) or 0
            ),
            "backfill_submission_throughput_submission_unresolved_count": int(
                backfill_submission_execution_focus.get("submission_consumption_unresolved_submission_count", 0) or 0
            ),
            "backfill_submission_queue_status": str(backfill_submission_queue_report.get("queue_status", "unknown")),
            "backfill_submission_queue_warning_codes": backfill_submission_queue_report.get("warning_codes", []),
            "backfill_submission_queue_total_item_count": int(
                backfill_submission_queue_summary.get("total_item_count", 0) or 0
            ),
            "backfill_submission_queue_pending_item_count": int(
                backfill_submission_queue_summary.get("pending_item_count", 0) or 0
            ),
            "backfill_submission_queue_blocked_item_count": int(
                backfill_submission_queue_summary.get("blocked_item_count", 0) or 0
            ),
            "backfill_submission_queue_pending_item_count_by_modality": backfill_submission_queue_summary.get(
                "pending_item_count_by_modality",
                {},
            ),
            "backfill_submission_queue_blocked_item_count_by_modality": backfill_submission_queue_summary.get(
                "blocked_item_count_by_modality",
                {},
            ),
            "backfill_submission_queue_item_action_plan_status": str(
                backfill_submission_queue_summary.get("action_plan_status", "unknown")
            ),
            "backfill_submission_queue_item_action_plan_blockers": backfill_submission_queue_summary.get(
                "action_plan_blockers",
                [],
            ),
            "backfill_submission_queue_item_priority_modalities": backfill_submission_queue_summary.get(
                "priority_modalities",
                [],
            ),
            "backfill_submission_queue_item_pending_submission_action_count": int(
                backfill_submission_queue_summary.get("pending_submission_action_count", 0) or 0
            ),
            "backfill_submission_queue_item_recommended_submission_action_count": int(
                backfill_submission_queue_summary.get("recommended_submission_action_count", 0) or 0
            ),
            "backfill_submission_queue_items": backfill_submission_queue_report.get("queue_items", []),
            "backfill_submission_queue_refresh_interval_hours": float(
                backfill_submission_queue_refresh_cadence.get("refresh_interval_hours", 0.0) or 0.0
            ),
            "backfill_submission_queue_refresh_cadence_status": str(
                backfill_submission_queue_refresh_cadence.get("cadence_status", "unknown")
            ),
            "backfill_submission_queue_refresh_previous_generated_at_utc": str(
                backfill_submission_queue_refresh_cadence.get("previous_queue_generated_at_utc", "")
            ),
            "backfill_submission_queue_refresh_next_due_utc": str(
                backfill_submission_queue_refresh_cadence.get("next_refresh_due_utc", "")
            ),
            "backfill_submission_queue_refresh_due_in_hours": float(
                backfill_submission_queue_refresh_cadence.get("due_in_hours", 0.0) or 0.0
            ),
            "backfill_submission_queue_refresh_evaluated_at_utc": str(
                backfill_submission_queue_refresh_cadence.get("evaluated_at_utc", "")
            ),
            "backfill_submission_queue_completion_status": str(
                backfill_submission_queue_completion_report.get("completion_status", "unknown")
            ),
            "backfill_submission_queue_completion_progress_status": str(
                backfill_submission_queue_completion_report.get("completion_progress_status", "unknown")
            ),
            "backfill_submission_queue_cycle_verification_status": str(
                backfill_submission_queue_completion_report.get("cycle_verification_status", "unknown")
            ),
            "backfill_submission_queue_completion_warning_codes": backfill_submission_queue_completion_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_completion_submitted_item_count": int(
                backfill_submission_queue_completion_counts.get("submitted_item_count", 0) or 0
            ),
            "backfill_submission_queue_completion_closed_item_count": int(
                backfill_submission_queue_completion_counts.get("closed_item_count", 0) or 0
            ),
            "backfill_submission_queue_completion_open_item_count": int(
                backfill_submission_queue_completion_counts.get("open_item_count", 0) or 0
            ),
            "backfill_submission_queue_completion_missing_handoff_item_count": int(
                backfill_submission_queue_completion_counts.get("missing_handoff_item_count", 0) or 0
            ),
            "backfill_submission_queue_completion_unknown_transition_item_count": int(
                backfill_submission_queue_completion_counts.get("unknown_transition_item_count", 0) or 0
            ),
            "backfill_submission_queue_cycle_net_new_movement_verified": bool(
                backfill_submission_queue_cycle_verification.get("net_new_movement_verified", False)
            ),
            "backfill_submission_queue_cycle_throughput_net_new_loop_count": int(
                backfill_submission_queue_cycle_verification.get("throughput_net_new_loop_count", 0) or 0
            ),
            "backfill_submission_queue_cycle_throughput_net_new_loop_ids": backfill_submission_queue_cycle_verification.get(
                "throughput_net_new_loop_ids",
                [],
            ),
            "backfill_submission_queue_cycle_submitted_item_delta_from_previous_cycle": int(
                backfill_submission_queue_cycle_verification.get(
                    "submitted_item_delta_from_previous_cycle",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_cycle_closed_item_delta_from_previous_cycle": int(
                backfill_submission_queue_cycle_verification.get(
                    "closed_item_delta_from_previous_cycle",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_cycle_open_item_delta_from_previous_cycle": int(
                backfill_submission_queue_cycle_verification.get(
                    "open_item_delta_from_previous_cycle",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_completion_transition_records": backfill_submission_queue_completion_report.get(
                "queue_transition_records",
                [],
            ),
            "backfill_submission_queue_commitment_status": str(
                backfill_submission_queue_commitments_report.get("commitment_status", "unknown")
            ),
            "backfill_submission_queue_cadence_run_obligation_status": str(
                backfill_submission_queue_commitments_report.get("cadence_run_obligation_status", "unknown")
            ),
            "backfill_submission_queue_commitment_total_count": int(
                backfill_submission_queue_commitment_counts.get("total_commitment_count", 0) or 0
            ),
            "backfill_submission_queue_commitment_pending_submission_count": int(
                backfill_submission_queue_commitment_counts.get("pending_submission_count", 0) or 0
            ),
            "backfill_submission_queue_commitment_pending_acknowledgement_count": int(
                backfill_submission_queue_commitment_counts.get("pending_acknowledgement_count", 0) or 0
            ),
            "backfill_submission_queue_commitment_blocked_submission_errors_count": int(
                backfill_submission_queue_commitment_counts.get("blocked_submission_errors_count", 0) or 0
            ),
            "backfill_submission_queue_commitment_escalation_required_count": int(
                backfill_submission_queue_commitment_counts.get("escalation_required_count", 0) or 0
            ),
            "backfill_submission_queue_commitment_rebuild_required_count": int(
                backfill_submission_queue_commitment_counts.get("rebuild_required_count", 0) or 0
            ),
            "backfill_submission_queue_owner_commitment_counts": backfill_submission_queue_commitments_report.get(
                "owner_commitment_counts",
                {},
            ),
            "backfill_submission_queue_unresolved_execution_blockers": backfill_submission_queue_commitments_report.get(
                "unresolved_execution_blockers",
                [],
            ),
            "backfill_submission_queue_commitment_rows": backfill_submission_queue_commitments_report.get(
                "commitment_rows",
                [],
            ),
            "backfill_submission_queue_commitment_cycle_snapshot": backfill_submission_queue_commitment_cycle_snapshot,
            "backfill_submission_queue_commitment_closure_status": str(
                backfill_submission_queue_commitment_closure_report.get("commitment_closure_status", "unknown")
            ),
            "backfill_submission_queue_commitment_cadence_run_closure_status": str(
                backfill_submission_queue_commitment_closure_report.get(
                    "cadence_run_closure_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_commitment_closure_warning_codes": backfill_submission_queue_commitment_closure_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_commitment_closure_total_count": int(
                backfill_submission_queue_commitment_closure_counts.get("total_commitment_count", 0) or 0
            ),
            "backfill_submission_queue_commitment_closure_closed_with_acknowledgement_count": int(
                backfill_submission_queue_commitment_closure_counts.get(
                    "closed_with_acknowledgement_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_commitment_closure_active_count": int(
                backfill_submission_queue_commitment_closure_counts.get("active_commitment_count", 0) or 0
            ),
            "backfill_submission_queue_commitment_stale_rollover_count": int(
                backfill_submission_queue_commitment_closure_counts.get("stale_rollover_count", 0) or 0
            ),
            "backfill_submission_queue_commitment_net_new_closed_with_acknowledgement_count": int(
                backfill_submission_queue_commitment_closure_counts.get(
                    "net_new_closed_with_acknowledgement_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_commitment_closure_rows": backfill_submission_queue_commitment_closure_report.get(
                "commitment_closure_rows",
                [],
            ),
            "backfill_submission_queue_commitment_closure_acknowledgement_rows": backfill_submission_queue_commitment_closure_report.get(
                "closure_acknowledgement_rows",
                [],
            ),
            "backfill_submission_queue_commitment_stale_rollover_rows": backfill_submission_queue_commitment_closure_report.get(
                "stale_rollover_rows",
                [],
            ),
            "backfill_submission_queue_followup_status": str(
                backfill_submission_queue_followup_report.get("followup_status", "unknown")
            ),
            "backfill_submission_queue_followup_warning_codes": backfill_submission_queue_followup_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_commitment_closure_status_gl40": str(
                backfill_submission_queue_followup_report.get("commitment_closure_status_gl40", "unknown")
            ),
            "backfill_submission_queue_followup_cadence_run_closure_status_gl40": str(
                backfill_submission_queue_followup_report.get("cadence_run_closure_status_gl40", "unknown")
            ),
            "backfill_submission_queue_followup_closure_warning_codes_gl40": backfill_submission_queue_followup_report.get(
                "closure_warning_codes_gl40",
                [],
            ),
            "backfill_submission_queue_followup_total_action_count": int(
                backfill_submission_queue_followup_counts.get("total_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_open_action_count": int(
                backfill_submission_queue_followup_counts.get("open_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_closed_action_count": int(
                backfill_submission_queue_followup_counts.get("closed_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_stale_rollover_action_count": int(
                backfill_submission_queue_followup_counts.get("stale_rollover_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_acknowledgement_completion_action_count": int(
                backfill_submission_queue_followup_counts.get("acknowledgement_completion_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_acknowledgement_closed_action_count": int(
                backfill_submission_queue_followup_counts.get("acknowledgement_closed_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_blocked_action_count": int(
                backfill_submission_queue_followup_counts.get("blocked_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_owner_counts": backfill_submission_queue_followup_report.get(
                "owner_followup_counts",
                {},
            ),
            "backfill_submission_queue_followup_action_rows": backfill_submission_queue_followup_report.get(
                "followup_action_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_status": str(
                backfill_submission_queue_followup_resolution_report.get("followup_resolution_status", "unknown")
            ),
            "backfill_submission_queue_followup_resolution_warning_codes": backfill_submission_queue_followup_resolution_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_total_action_count": int(
                backfill_submission_queue_followup_resolution_counts.get("total_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_open_action_count_gl41": int(
                backfill_submission_queue_followup_resolution_counts.get("open_action_count_gl41", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_closed_action_count_gl41": int(
                backfill_submission_queue_followup_resolution_counts.get("closed_action_count_gl41", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_resolved_action_count": int(
                backfill_submission_queue_followup_resolution_counts.get("resolved_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_in_progress_action_count": int(
                backfill_submission_queue_followup_resolution_counts.get("in_progress_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_unresolved_action_count": int(
                backfill_submission_queue_followup_resolution_counts.get("unresolved_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_submission_linked_action_count": int(
                backfill_submission_queue_followup_resolution_counts.get("submission_linked_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_closure_acknowledged_action_count": int(
                backfill_submission_queue_followup_resolution_counts.get("closure_acknowledged_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_consumed_submission_action_count": int(
                backfill_submission_queue_followup_resolution_counts.get("consumed_submission_action_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_submission_invalid_count": int(
                backfill_submission_queue_followup_resolution_counts.get(
                    "submission_consumption_invalid_submission_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_submission_unresolved_count": int(
                backfill_submission_queue_followup_resolution_counts.get(
                    "submission_consumption_unresolved_submission_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_owner_counts": backfill_submission_queue_followup_resolution_report.get(
                "owner_followup_resolution_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_rows": backfill_submission_queue_followup_resolution_report.get(
                "followup_resolution_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_status": str(
                backfill_submission_queue_followup_resolution_escalations_report.get(
                    "followup_resolution_escalation_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_warning_codes": backfill_submission_queue_followup_resolution_escalations_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalations_counts.get("total_item_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalations_counts.get("open_item_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_blocked_item_count": int(
                backfill_submission_queue_followup_resolution_escalations_counts.get("blocked_item_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_pending_ack_item_count": int(
                backfill_submission_queue_followup_resolution_escalations_counts.get(
                    "pending_ack_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_active_item_count": int(
                backfill_submission_queue_followup_resolution_escalations_counts.get("active_item_count", 0) or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_owner_counts": backfill_submission_queue_followup_resolution_escalations_report.get(
                "owner_followup_resolution_escalation_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_rows": backfill_submission_queue_followup_resolution_escalations_report.get(
                "followup_resolution_escalation_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_acknowledgement_status": str(
                backfill_submission_queue_followup_resolution_escalation_acknowledgements_report.get(
                    "followup_resolution_escalation_acknowledgement_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_acknowledgement_warning_codes": backfill_submission_queue_followup_resolution_escalation_acknowledgements_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_acknowledgement_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_acknowledgements_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_acknowledgement_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_acknowledgements_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_acknowledgement_resolved_acknowledged_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_acknowledgements_counts.get(
                    "resolved_acknowledged_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_acknowledgement_pending_ack_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_acknowledgements_counts.get(
                    "pending_ack_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_acknowledgement_blocked_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_acknowledgements_counts.get(
                    "blocked_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_acknowledgement_owner_counts": backfill_submission_queue_followup_resolution_escalation_acknowledgements_report.get(
                "owner_followup_resolution_escalation_acknowledgement_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_acknowledgement_rows": backfill_submission_queue_followup_resolution_escalation_acknowledgements_report.get(
                "followup_resolution_escalation_acknowledgement_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_throughput_status": str(
                backfill_submission_queue_followup_resolution_escalation_throughput_report.get(
                    "followup_resolution_escalation_throughput_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_throughput_warning_codes": backfill_submission_queue_followup_resolution_escalation_throughput_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_acknowledged_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_throughput_delta.get(
                    "net_new_resolved_acknowledged_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_count": int(
                backfill_submission_queue_followup_resolution_escalation_throughput_delta.get(
                    "net_new_resolved_submission_loop_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_count": int(
                backfill_submission_queue_followup_resolution_escalation_throughput_delta.get(
                    "net_new_launch_gate_eligible_loop_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_ack_closed_loop_count": int(
                backfill_submission_queue_followup_resolution_escalation_throughput_delta.get(
                    "unresolved_ack_closed_loop_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_throughput_unresolved_acknowledged_submission_loop_ids": backfill_submission_queue_followup_resolution_escalation_throughput_report.get(
                "unresolved_acknowledged_submission_loop_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_resolved_submission_loop_ids": backfill_submission_queue_followup_resolution_escalation_throughput_report.get(
                "net_new_resolved_submission_loop_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_throughput_net_new_launch_gate_eligible_loop_ids": backfill_submission_queue_followup_resolution_escalation_throughput_report.get(
                "net_new_launch_gate_eligible_loop_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_report.get(
                    "followup_resolution_escalation_action_plan_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_total_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_counts.get(
                    "total_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_open_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_counts.get(
                    "open_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closed_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_counts.get(
                    "closed_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_unresolved_ack_mapping_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_counts.get(
                    "unresolved_ack_mapping_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_recommended_backfill_slot_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_counts.get(
                    "recommended_backfill_slot_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_report.get(
                "followup_resolution_escalation_action_plan_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report.get(
                    "followup_resolution_escalation_action_plan_closure_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_total_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts.get(
                    "total_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_open_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts.get(
                    "open_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_closed_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts.get(
                    "closed_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_carried_open_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts.get(
                    "carried_open_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_closed_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts.get(
                    "net_new_closed_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_stale_open_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts.get(
                    "stale_open_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_launch_gate_eligible_loop_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_counts.get(
                    "net_new_launch_gate_eligible_loop_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_open_action_count_delta": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_delta.get(
                    "open_action_count_delta",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_carried_open_action_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report.get(
                "carried_open_action_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_closed_action_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report.get(
                "net_new_closed_action_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_net_new_launch_gate_eligible_loop_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report.get(
                "net_new_launch_gate_eligible_loop_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_total_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_counts.get(
                    "total_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_open_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_counts.get(
                    "open_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_stale_open_action_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_counts.get(
                    "stale_open_action_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_stall_cycle_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_counts.get(
                    "stall_cycle_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_overdue_stalled_cycles_threshold": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_counts.get(
                    "overdue_stalled_cycles_threshold",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh_interval_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh.get(
                    "refresh_interval_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_state": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh.get(
                    "cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_previous_generated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh.get(
                    "previous_generated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_next_refresh_due_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh.get(
                    "next_refresh_due_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_due_in_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh.get(
                    "due_in_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_evaluated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_refresh.get(
                    "evaluated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_blocked_overdue_stalled_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts.get(
                    "blocked_overdue_stalled_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_due_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts.get(
                    "due_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_monitor_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts.get(
                    "monitor_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_cadence_stall_cycle_count_gl48": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts.get(
                    "cadence_stall_cycle_count_gl48",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl48": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts.get(
                    "cadence_overdue_stalled_cycles_threshold_gl48",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_escalate_after_due_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_counts.get(
                    "escalate_after_due_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_owner_counts": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report.get(
                "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts.get(
                    "closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_with_ack_record_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts.get(
                    "escalation_rows_with_acknowledgement_record_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_with_matching_ack_loop_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts.get(
                    "escalation_rows_with_matching_ack_loop_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_with_mismatched_ack_loop_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts.get(
                    "escalation_rows_with_mismatched_ack_loop_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_missing_ack_record_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts.get(
                    "escalation_rows_missing_acknowledgement_record_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_without_handoff_queue_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts.get(
                    "escalation_rows_without_handoff_queue_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_unreferenced_acknowledgement_record_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts.get(
                    "unreferenced_acknowledgement_record_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_owner_counts": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report.get(
                "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_present": bool(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot.get(
                    "input_present",
                    False,
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_path": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot.get(
                    "input_path",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_acknowledgement_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot.get(
                    "input_acknowledgement_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_valid_acknowledgement_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot.get(
                    "valid_acknowledgement_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_invalid_acknowledgement_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot.get(
                    "invalid_acknowledgement_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_invalid_acknowledgement_records": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot.get(
                "invalid_acknowledgement_records",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_unreferenced_acknowledgement_records": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_input_snapshot.get(
                "unreferenced_acknowledgement_records",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_previous_open_item_count_gl50": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "previous_open_item_count_gl50",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_carried_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "carried_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_stale_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "stale_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_ack_loop_mismatch_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "ack_loop_mismatch_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_ack_missing_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "ack_missing_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_missing_handoff_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "missing_handoff_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_launch_gate_eligible_loop_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "net_new_launch_gate_eligible_loop_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_open_item_count_delta": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_counts.get(
                    "open_item_count_delta",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_carried_open_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report.get(
                "carried_open_acknowledgement_ingestion_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report.get(
                "net_new_closed_acknowledgement_ingestion_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_net_new_launch_gate_eligible_loop_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report.get(
                "net_new_launch_gate_eligible_loop_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_stale_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts.get(
                    "stale_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_net_new_closed_item_count_gl51": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts.get(
                    "net_new_closed_item_count_gl51",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_net_new_launch_gate_eligible_loop_count_gl51": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts.get(
                    "net_new_launch_gate_eligible_loop_count_gl51",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_stall_cycle_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts.get(
                    "stall_cycle_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_overdue_stalled_cycles_threshold": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_counts.get(
                    "overdue_stalled_cycles_threshold",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh_interval_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh.get(
                    "refresh_interval_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_state": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh.get(
                    "cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_previous_generated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh.get(
                    "previous_generated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_next_refresh_due_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh.get(
                    "next_refresh_due_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_due_in_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh.get(
                    "due_in_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_evaluated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_refresh.get(
                    "evaluated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_blocked_overdue_stalled_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts.get(
                    "blocked_overdue_stalled_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_due_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts.get(
                    "due_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_monitor_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts.get(
                    "monitor_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_cadence_stall_cycle_count_gl52": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts.get(
                    "cadence_stall_cycle_count_gl52",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl52": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts.get(
                    "cadence_overdue_stalled_cycles_threshold_gl52",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_escalate_after_due_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_counts.get(
                    "escalate_after_due_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_owner_counts": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report.get(
                "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_previous_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "previous_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "carried_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_stale_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "stale_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "net_new_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_count_gl50": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "net_new_closed_backed_by_ack_ingestion_item_count_gl50",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_count_gl50": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "net_new_closed_without_ack_ingestion_item_count_gl50",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_ack_ingestion_closed_item_count_gl50": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "ack_ingestion_closed_item_count_gl50",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_ack_ingestion_open_item_count_gl50": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts.get(
                    "ack_ingestion_open_item_count_gl50",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_owner_counts": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
                "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_carried_open_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_open_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_ids_gl50": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_backed_by_ack_ingestion_item_ids_gl50",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_ids_gl50": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_net_new_closed_without_ack_ingestion_item_ids_gl50",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_stale_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts.get(
                    "stale_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_net_new_closed_item_count_gl54": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts.get(
                    "net_new_closed_item_count_gl54",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_net_new_closed_backed_by_ack_ingestion_item_count_gl50": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts.get(
                    "net_new_closed_backed_by_ack_ingestion_item_count_gl50",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_stall_cycle_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts.get(
                    "stall_cycle_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles_threshold": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_counts.get(
                    "overdue_stalled_cycles_threshold",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh_interval_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh.get(
                    "refresh_interval_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_state": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh.get(
                    "cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_previous_generated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh.get(
                    "previous_generated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_next_refresh_due_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh.get(
                    "next_refresh_due_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_due_in_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh.get(
                    "due_in_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_evaluated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_refresh.get(
                    "evaluated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_blocked_overdue_stalled_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "blocked_overdue_stalled_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_due_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "due_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_monitor_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "monitor_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_cadence_stall_cycle_count_gl55": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "cadence_stall_cycle_count_gl55",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl55": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "cadence_overdue_stalled_cycles_threshold_gl55",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_escalate_after_due_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "escalate_after_due_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_owner_counts": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report.get(
                "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_previous_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "previous_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "carried_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_stale_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "stale_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "net_new_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl54_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "net_new_closed_backed_by_gl54_net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl54_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "net_new_closed_without_gl54_net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "gl54_net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_action_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "gl54_net_new_closed_action_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_owner_counts": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl54_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl54_net_new_closed_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl54_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl54_net_new_closed_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_gl54_net_new_closed_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stale_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "stale_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_item_count_gl57": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "net_new_closed_item_count_gl57",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_backed_by_gl54_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "net_new_closed_backed_by_gl54_net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stall_cycle_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "stall_cycle_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles_threshold": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "overdue_stalled_cycles_threshold",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh_interval_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "refresh_interval_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_state": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_previous_generated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "previous_generated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_next_refresh_due_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "next_refresh_due_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_due_in_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "due_in_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_evaluated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "evaluated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_blocked_overdue_stalled_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "blocked_overdue_stalled_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_due_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "due_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_monitor_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "monitor_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_cadence_stall_cycle_count_gl58": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "cadence_stall_cycle_count_gl58",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl58": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "cadence_overdue_stalled_cycles_threshold_gl58",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_escalate_after_due_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "escalate_after_due_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_owner_counts": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
                "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_previous_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "previous_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "carried_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_stale_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "stale_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "net_new_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl57_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "net_new_closed_backed_by_gl57_net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl57_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "net_new_closed_without_gl57_net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "gl57_net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_action_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts.get(
                    "gl57_net_new_closed_action_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_owner_counts": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_carried_open_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_open_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl57_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_backed_by_gl57_net_new_closed_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl57_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_net_new_closed_without_gl57_net_new_closed_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_item_ids": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_gl57_net_new_closed_item_ids",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stale_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "stale_open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_item_count_gl60": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "net_new_closed_item_count_gl60",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_net_new_closed_backed_by_gl57_net_new_closed_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "net_new_closed_backed_by_gl57_net_new_closed_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_stall_cycle_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "stall_cycle_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_overdue_stalled_cycles_threshold": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_counts.get(
                    "overdue_stalled_cycles_threshold",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh_interval_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "refresh_interval_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_state": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "cadence_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_previous_generated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "previous_generated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_next_refresh_due_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "next_refresh_due_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_due_in_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "due_in_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_evaluated_at_utc": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_refresh.get(
                    "evaluated_at_utc",
                    "",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_rows",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status": str(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
                    "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_status",
                    "unknown",
                )
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_warning_codes": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
                "warning_codes",
                [],
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_total_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "total_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_open_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "open_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_blocked_overdue_stalled_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "blocked_overdue_stalled_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_due_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "due_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_monitor_item_count": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "monitor_item_count",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_cadence_stall_cycle_count_gl61": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "cadence_stall_cycle_count_gl61",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_cadence_overdue_stalled_cycles_threshold_gl61": int(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "cadence_overdue_stalled_cycles_threshold_gl61",
                    0,
                )
                or 0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_escalate_after_due_hours": float(
                backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_counts.get(
                    "escalate_after_due_hours",
                    0.0,
                )
                or 0.0
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_owner_counts": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
                "owner_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_counts",
                {},
            ),
            "backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_rows": backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report.get(
                "followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_rows",
                [],
            ),
            "backfill_submission_ingestion_replay_applied": bool(
                getattr(args, "backfill_submission_ingestion_replay_applied", False)
            ),
            "backfill_submission_ingestion_consumed_loop_count": int(
                getattr(args, "backfill_submission_ingestion_consumed_loop_count", 0) or 0
            ),
            "backfill_submission_ingestion_status": str(
                getattr(args, "backfill_submission_ingestion_status", "unknown")
            ),
            "backfill_handoff_status": str(backfill_handoff_report.get("handoff_status", "unknown")),
            "backfill_handoff_total_queue_item_count": int(
                backfill_handoff_counts.get("total_queue_item_count", 0) or 0
            ),
            "backfill_handoff_open_queue_item_count": int(
                backfill_handoff_counts.get("open_queue_item_count", 0) or 0
            ),
            "backfill_handoff_submission_linked_pending_ack_count": int(
                backfill_handoff_counts.get("submission_linked_pending_ack_count", 0) or 0
            ),
            "backfill_handoff_closure_acknowledged_count": int(
                backfill_handoff_counts.get("closure_acknowledged_count", 0) or 0
            ),
            "backfill_handoff_owner": str(args.backfill_handoff_owner).strip() or "controlled-beta-ops",
            "backfill_handoff_submission_linkage_strategy_counts": backfill_handoff_submission_linkage_snapshot.get(
                "linkage_strategy_counts",
                {},
            ),
            "backfill_handoff_submission_unlinked_count": int(
                backfill_handoff_submission_linkage_snapshot.get("unlinked_submission_count", 0) or 0
            ),
            "backfill_handoff_submission_unlinked_records": backfill_handoff_submission_linkage_snapshot.get(
                "unlinked_submissions",
                [],
            ),
            "backfill_handoff_acknowledgement_input_count": int(
                backfill_handoff_ack_snapshot.get("input_acknowledgement_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_valid_count": int(
                backfill_handoff_ack_snapshot.get("valid_acknowledgement_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_invalid_count": int(
                backfill_handoff_ack_snapshot.get("invalid_acknowledgement_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_invalid_records": backfill_handoff_ack_snapshot.get(
                "invalid_acknowledgement_records",
                [],
            ),
            "backfill_handoff_acknowledgement_sla_status": str(
                backfill_handoff_ack_sla_snapshot.get("acknowledgement_sla_status", "unknown")
            ),
            "backfill_handoff_acknowledgement_sla_hours": float(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_sla_hours", 0.0) or 0.0
            ),
            "backfill_handoff_acknowledgement_overdue_hours": float(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_overdue_hours", 0.0) or 0.0
            ),
            "backfill_handoff_acknowledgement_sla_evaluation_timestamp_utc": str(
                backfill_handoff_ack_sla_snapshot.get("evaluation_timestamp_utc", "")
            ),
            "backfill_handoff_acknowledgement_within_sla_count": int(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_within_sla_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_sla_breached_count": int(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_sla_breached_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_overdue_count": int(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_overdue_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_tracking_incomplete_count": int(
                backfill_handoff_ack_sla_snapshot.get("pending_ack_missing_reference_timestamp_count", 0) or 0
            ),
            "backfill_handoff_acknowledgement_sla_breached_queue_items": backfill_handoff_ack_sla_snapshot.get(
                "pending_ack_sla_breached_queue_items",
                [],
            ),
            "backfill_handoff_acknowledgement_overdue_queue_items": backfill_handoff_ack_sla_snapshot.get(
                "pending_ack_overdue_queue_items",
                [],
            ),
            "backfill_handoff_acknowledgement_tracking_incomplete_queue_items": backfill_handoff_ack_sla_snapshot.get(
                "pending_ack_tracking_incomplete_queue_items",
                [],
            ),
            "backfill_handoff_escalation_status": str(
                backfill_handoff_escalations_report.get("escalation_status", "unknown")
            ),
            "backfill_handoff_escalation_owner": str(
                backfill_handoff_escalations_report.get("owner", "")
            )
            or (str(args.backfill_handoff_escalations_owner).strip() or "controlled-beta-ops"),
            "backfill_handoff_escalation_total_item_count": int(
                backfill_handoff_escalation_counts.get("total_escalation_item_count", 0) or 0
            ),
            "backfill_handoff_escalation_sla_breached_item_count": int(
                backfill_handoff_escalation_counts.get("sla_breached_item_count", 0) or 0
            ),
            "backfill_handoff_escalation_overdue_item_count": int(
                backfill_handoff_escalation_counts.get("overdue_item_count", 0) or 0
            ),
            "backfill_handoff_escalation_tracking_incomplete_item_count": int(
                backfill_handoff_escalation_counts.get("tracking_incomplete_item_count", 0) or 0
            ),
            "backfill_handoff_escalation_sla_breached_items": backfill_handoff_escalation_exports.get(
                "sla_breached_items",
                [],
            ),
            "backfill_handoff_escalation_overdue_items": backfill_handoff_escalation_exports.get(
                "overdue_items",
                [],
            ),
            "backfill_handoff_escalation_tracking_incomplete_items": backfill_handoff_escalation_exports.get(
                "tracking_incomplete_items",
                [],
            ),
        },
        "safety_summary": {
            "unreviewed_published_count": int(safety.get("unreviewed_published_count", 0) or 0),
            "critical_secret_or_pii_leak_count": int(safety.get("critical_secret_or_pii_leak_count", 0) or 0),
            "high_severity_incident_count": int(safety.get("high_severity_incident_count", 0) or 0),
        },
        "gate_summary": {
            "failed_checks": failed_checks,
            "blocking_check_count": len(failed_checks),
        },
        "policy_notes": [
            "This pack summarizes controlled external Beta evidence only.",
            "Fixture or synthetic loops are not launch-gate-eligible real evidence.",
            "No GA claim is allowed unless launch_readiness decision and gate checks support it.",
        ],
    }
    _normalize_evidence_pack_paths(evidence_pack)
    evidence_pack["path_hygiene"] = _build_path_hygiene(evidence_pack)
    return evidence_pack


def main() -> int:
    args = _parse_args()
    args.backfill_submission_ingestion_replay_applied = False
    args.backfill_submission_ingestion_replay_manifest_paths = []
    args.backfill_submission_ingestion_consumed_loop_count = 0
    args.backfill_submission_ingestion_status = "NO_CONSUMPTION_DATA"
    run_report_values = [str(value).strip() for value in args.run_report if str(value).strip()]
    loop_manifest_values = [str(value).strip() for value in args.loop_manifest if str(value).strip()]
    loop_manifest_dir_values = [str(value).strip() for value in args.loop_manifest_dir if str(value).strip()]
    run_report_paths = [Path(value).resolve() for value in run_report_values]
    try:
        loop_manifest_paths, loop_manifest_dirs = _resolve_loop_manifest_paths(
            explicit_paths=loop_manifest_values,
            manifest_dirs=loop_manifest_dir_values,
            pattern=str(args.loop_manifest_pattern),
            recursive=bool(args.loop_manifest_recursive),
        )
    except ValueError as exc:
        print("Real-trial launch evidence pipeline failed: %s" % exc, file=sys.stderr)
        return 2
    if (loop_manifest_values or loop_manifest_dir_values) and not loop_manifest_paths:
        print(
            "Real-trial launch evidence pipeline failed: %s"
            % _format_no_loop_manifest_matches_message(
                manifest_dirs=loop_manifest_dirs,
                pattern=str(args.loop_manifest_pattern),
                recursive=bool(args.loop_manifest_recursive),
            ),
            file=sys.stderr,
        )
        return 2
    if not run_report_paths and not loop_manifest_paths and not loop_manifest_dirs:
        run_report_paths = [DEFAULT_RUN_REPORT]
    missing_inputs = [path for path in run_report_paths if not path.is_file()]
    missing_inputs.extend(path for path in loop_manifest_paths if not path.is_file())
    if missing_inputs:
        print(
            "Real-trial launch evidence pipeline failed: missing loop evidence input(s): %s"
            % ", ".join(str(path) for path in missing_inputs),
            file=sys.stderr,
        )
        return 2

    try:
        manifest_output = _resolve_required_output_path(
            args.real_trial_manifest_output,
            name="real-trial-manifest-output",
        )
        trial_metrics_output = _resolve_required_output_path(
            args.trial_metrics_report_output,
            name="trial-metrics-report-output",
        )
        launch_readiness_output = _resolve_required_output_path(
            args.launch_readiness_output,
            name="launch-readiness-output",
        )
        evidence_pack_output = _resolve_required_output_path(
            args.evidence_pack_output,
            name="evidence-pack-output",
        )
    except ValueError as exc:
        print("Real-trial launch evidence pipeline failed: %s" % exc, file=sys.stderr)
        return 2

    controlled_trial_run_report_value = str(args.controlled_trial_run_report).strip()
    controlled_trial_run_report = (
        Path(controlled_trial_run_report_value).resolve()
        if controlled_trial_run_report_value
        else (run_report_paths[0] if run_report_paths else DEFAULT_RUN_REPORT)
    )

    collection_command = _build_collection_command(args, run_report_paths, manifest_output)
    collection_result = _run_command(collection_command)
    _print_command_output("real-trial-loop-collection", collection_result)
    if collection_result.returncode != 0:
        return collection_result.returncode

    trial_metrics_command = _build_trial_metrics_command(args, manifest_output, trial_metrics_output)
    trial_metrics_result = _run_command(trial_metrics_command)
    _print_command_output("trial-metrics-collector", trial_metrics_result)
    if trial_metrics_result.returncode != 0:
        return trial_metrics_result.returncode

    backfill_execution_command = _build_backfill_execution_command(args)
    backfill_execution_result = _run_command(backfill_execution_command)
    _print_command_output("real-trial-backfill-execution", backfill_execution_result)
    if backfill_execution_result.returncode != 0:
        return backfill_execution_result.returncode

    backfill_intake_actions_command = _build_backfill_intake_actions_command(args)
    backfill_intake_actions_result = _run_command(backfill_intake_actions_command)
    _print_command_output("real-trial-backfill-intake-actions", backfill_intake_actions_result)
    if backfill_intake_actions_result.returncode != 0:
        return backfill_intake_actions_result.returncode

    backfill_submission_templates_command = _build_backfill_submission_templates_command(args)
    backfill_submission_templates_result = _run_command(backfill_submission_templates_command)
    _print_command_output("real-trial-backfill-submission-templates", backfill_submission_templates_result)
    if backfill_submission_templates_result.returncode != 0:
        return backfill_submission_templates_result.returncode

    backfill_submission_consumption_command = _build_backfill_submission_consumption_command(args)
    backfill_submission_consumption_result = _run_command(backfill_submission_consumption_command)
    _print_command_output("real-trial-backfill-submission-consumption", backfill_submission_consumption_result)
    if backfill_submission_consumption_result.returncode != 0:
        return backfill_submission_consumption_result.returncode

    backfill_submission_throughput_command = _build_backfill_submission_throughput_command(args)
    backfill_submission_throughput_result = _run_command(backfill_submission_throughput_command)
    _print_command_output("real-trial-backfill-submission-throughput", backfill_submission_throughput_result)
    if backfill_submission_throughput_result.returncode != 0:
        return backfill_submission_throughput_result.returncode

    backfill_submission_queue_command = _build_backfill_submission_queue_command(args)
    backfill_submission_queue_result = _run_command(backfill_submission_queue_command)
    _print_command_output("real-trial-backfill-submission-queue", backfill_submission_queue_result)
    if backfill_submission_queue_result.returncode != 0:
        return backfill_submission_queue_result.returncode

    try:
        consumption_status, consumed_loop_count = _read_submission_consumption_status(
            Path(args.backfill_submission_consumption_output).resolve()
        )
        args.backfill_submission_ingestion_status = consumption_status or "unknown"
        args.backfill_submission_ingestion_consumed_loop_count = consumed_loop_count
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            "Real-trial launch evidence pipeline failed while reading submission-consumption report: %s" % exc,
            file=sys.stderr,
        )
        return 2

    consumed_manifest_path = Path(args.backfill_submission_consumed_manifest_output).resolve()
    if args.backfill_submission_ingestion_consumed_loop_count > 0:
        if not consumed_manifest_path.is_file():
            print(
                "Real-trial launch evidence pipeline failed: consumed-manifest replay required but missing file: %s"
                % consumed_manifest_path,
                file=sys.stderr,
            )
            return 2
        replay_collection_command = _build_collection_command(
            args,
            run_report_paths,
            manifest_output,
            extra_loop_manifest_paths=[consumed_manifest_path],
        )
        replay_collection_result = _run_command(replay_collection_command)
        _print_command_output("real-trial-loop-collection-replay", replay_collection_result)
        if replay_collection_result.returncode != 0:
            return replay_collection_result.returncode

        replay_trial_metrics_command = _build_trial_metrics_command(args, manifest_output, trial_metrics_output)
        replay_trial_metrics_result = _run_command(replay_trial_metrics_command)
        _print_command_output("trial-metrics-collector-replay", replay_trial_metrics_result)
        if replay_trial_metrics_result.returncode != 0:
            return replay_trial_metrics_result.returncode

        replay_backfill_execution_command = _build_backfill_execution_command(args)
        replay_backfill_execution_result = _run_command(replay_backfill_execution_command)
        _print_command_output("real-trial-backfill-execution-replay", replay_backfill_execution_result)
        if replay_backfill_execution_result.returncode != 0:
            return replay_backfill_execution_result.returncode

        replay_backfill_intake_actions_command = _build_backfill_intake_actions_command(args)
        replay_backfill_intake_actions_result = _run_command(replay_backfill_intake_actions_command)
        _print_command_output("real-trial-backfill-intake-actions-replay", replay_backfill_intake_actions_result)
        if replay_backfill_intake_actions_result.returncode != 0:
            return replay_backfill_intake_actions_result.returncode

        replay_backfill_submission_templates_command = _build_backfill_submission_templates_command(args)
        replay_backfill_submission_templates_result = _run_command(replay_backfill_submission_templates_command)
        _print_command_output(
            "real-trial-backfill-submission-templates-replay",
            replay_backfill_submission_templates_result,
        )
        if replay_backfill_submission_templates_result.returncode != 0:
            return replay_backfill_submission_templates_result.returncode

        replay_backfill_submission_throughput_command = _build_backfill_submission_throughput_command(args)
        replay_backfill_submission_throughput_result = _run_command(replay_backfill_submission_throughput_command)
        _print_command_output(
            "real-trial-backfill-submission-throughput-replay",
            replay_backfill_submission_throughput_result,
        )
        if replay_backfill_submission_throughput_result.returncode != 0:
            return replay_backfill_submission_throughput_result.returncode

        replay_backfill_submission_queue_command = _build_backfill_submission_queue_command(args)
        replay_backfill_submission_queue_result = _run_command(replay_backfill_submission_queue_command)
        _print_command_output(
            "real-trial-backfill-submission-queue-replay",
            replay_backfill_submission_queue_result,
        )
        if replay_backfill_submission_queue_result.returncode != 0:
            return replay_backfill_submission_queue_result.returncode

        replay_backfill_handoff_command = _build_backfill_handoff_command(args)
        replay_backfill_handoff_result = _run_command(replay_backfill_handoff_command)
        _print_command_output("real-trial-backfill-handoff-replay", replay_backfill_handoff_result)
        if replay_backfill_handoff_result.returncode != 0:
            return replay_backfill_handoff_result.returncode

        replay_backfill_submission_queue_completion_command = _build_backfill_submission_queue_completion_command(args)
        replay_backfill_submission_queue_completion_result = _run_command(
            replay_backfill_submission_queue_completion_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-completion-replay",
            replay_backfill_submission_queue_completion_result,
        )
        if replay_backfill_submission_queue_completion_result.returncode != 0:
            return replay_backfill_submission_queue_completion_result.returncode

        replay_backfill_handoff_escalations_command = _build_backfill_handoff_escalations_command(args)
        replay_backfill_handoff_escalations_result = _run_command(replay_backfill_handoff_escalations_command)
        _print_command_output(
            "real-trial-backfill-handoff-escalations-replay",
            replay_backfill_handoff_escalations_result,
        )
        if replay_backfill_handoff_escalations_result.returncode != 0:
            return replay_backfill_handoff_escalations_result.returncode

        replay_backfill_submission_queue_commitments_command = _build_backfill_submission_queue_commitments_command(
            args
        )
        replay_backfill_submission_queue_commitments_result = _run_command(
            replay_backfill_submission_queue_commitments_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-commitments-replay",
            replay_backfill_submission_queue_commitments_result,
        )
        if replay_backfill_submission_queue_commitments_result.returncode != 0:
            return replay_backfill_submission_queue_commitments_result.returncode

        replay_backfill_submission_queue_commitment_closure_command = (
            _build_backfill_submission_queue_commitment_closure_command(args)
        )
        replay_backfill_submission_queue_commitment_closure_result = _run_command(
            replay_backfill_submission_queue_commitment_closure_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-commitment-closure-replay",
            replay_backfill_submission_queue_commitment_closure_result,
        )
        if replay_backfill_submission_queue_commitment_closure_result.returncode != 0:
            return replay_backfill_submission_queue_commitment_closure_result.returncode

        replay_backfill_submission_queue_followup_command = _build_backfill_submission_queue_followup_command(args)
        replay_backfill_submission_queue_followup_result = _run_command(
            replay_backfill_submission_queue_followup_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-replay",
            replay_backfill_submission_queue_followup_result,
        )
        if replay_backfill_submission_queue_followup_result.returncode != 0:
            return replay_backfill_submission_queue_followup_result.returncode

        replay_backfill_submission_queue_followup_resolution_command = (
            _build_backfill_submission_queue_followup_resolution_command(args)
        )
        replay_backfill_submission_queue_followup_resolution_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-replay",
            replay_backfill_submission_queue_followup_resolution_result,
        )
        if replay_backfill_submission_queue_followup_resolution_result.returncode != 0:
            return replay_backfill_submission_queue_followup_resolution_result.returncode

        replay_backfill_submission_queue_followup_resolution_escalations_command = (
            _build_backfill_submission_queue_followup_resolution_escalations_command(args)
        )
        replay_backfill_submission_queue_followup_resolution_escalations_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalations_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalations-replay",
            replay_backfill_submission_queue_followup_resolution_escalations_result,
        )
        if replay_backfill_submission_queue_followup_resolution_escalations_result.returncode != 0:
            return replay_backfill_submission_queue_followup_resolution_escalations_result.returncode

        replay_backfill_submission_queue_followup_resolution_escalation_acknowledgements_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_acknowledgements_command(args)
        )
        replay_backfill_submission_queue_followup_resolution_escalation_acknowledgements_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_acknowledgements_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-acknowledgements-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_acknowledgements_result,
        )
        if replay_backfill_submission_queue_followup_resolution_escalation_acknowledgements_result.returncode != 0:
            return replay_backfill_submission_queue_followup_resolution_escalation_acknowledgements_result.returncode

        replay_backfill_submission_queue_followup_resolution_escalation_throughput_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_throughput_command(args)
        )
        replay_backfill_submission_queue_followup_resolution_escalation_throughput_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_throughput_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-throughput-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_throughput_result,
        )
        if replay_backfill_submission_queue_followup_resolution_escalation_throughput_result.returncode != 0:
            return replay_backfill_submission_queue_followup_resolution_escalation_throughput_result.returncode

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_command(args)
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_result,
        )
        if replay_backfill_submission_queue_followup_resolution_escalation_action_plan_result.returncode != 0:
            return replay_backfill_submission_queue_followup_resolution_escalation_action_plan_result.returncode

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_command(args)
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_result,
        )
        if replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_result.returncode != 0:
            return replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_result.returncode

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_result.returncode
            )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result.returncode
            )

        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command = (
            _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command(
                args
            )
        )
        replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result = _run_command(
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command
        )
        _print_command_output(
            "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations-replay",
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result,
        )
        if (
            replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result.returncode
            != 0
        ):
            return (
                replay_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result.returncode
            )

        args.backfill_submission_ingestion_replay_applied = True
        args.backfill_submission_ingestion_replay_manifest_paths = [str(consumed_manifest_path)]

    backfill_handoff_command = _build_backfill_handoff_command(args)
    backfill_handoff_result = _run_command(backfill_handoff_command)
    _print_command_output("real-trial-backfill-handoff", backfill_handoff_result)
    if backfill_handoff_result.returncode != 0:
        return backfill_handoff_result.returncode

    backfill_submission_queue_completion_command = _build_backfill_submission_queue_completion_command(args)
    backfill_submission_queue_completion_result = _run_command(backfill_submission_queue_completion_command)
    _print_command_output(
        "real-trial-backfill-submission-queue-completion",
        backfill_submission_queue_completion_result,
    )
    if backfill_submission_queue_completion_result.returncode != 0:
        return backfill_submission_queue_completion_result.returncode

    backfill_handoff_escalations_command = _build_backfill_handoff_escalations_command(args)
    backfill_handoff_escalations_result = _run_command(backfill_handoff_escalations_command)
    _print_command_output("real-trial-backfill-handoff-escalations", backfill_handoff_escalations_result)
    if backfill_handoff_escalations_result.returncode != 0:
        return backfill_handoff_escalations_result.returncode

    backfill_submission_queue_commitments_command = _build_backfill_submission_queue_commitments_command(args)
    backfill_submission_queue_commitments_result = _run_command(backfill_submission_queue_commitments_command)
    _print_command_output(
        "real-trial-backfill-submission-queue-commitments",
        backfill_submission_queue_commitments_result,
    )
    if backfill_submission_queue_commitments_result.returncode != 0:
        return backfill_submission_queue_commitments_result.returncode

    backfill_submission_queue_commitment_closure_command = (
        _build_backfill_submission_queue_commitment_closure_command(args)
    )
    backfill_submission_queue_commitment_closure_result = _run_command(
        backfill_submission_queue_commitment_closure_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-commitment-closure",
        backfill_submission_queue_commitment_closure_result,
    )
    if backfill_submission_queue_commitment_closure_result.returncode != 0:
        return backfill_submission_queue_commitment_closure_result.returncode

    backfill_submission_queue_followup_command = _build_backfill_submission_queue_followup_command(args)
    backfill_submission_queue_followup_result = _run_command(backfill_submission_queue_followup_command)
    _print_command_output(
        "real-trial-backfill-submission-queue-followup",
        backfill_submission_queue_followup_result,
    )
    if backfill_submission_queue_followup_result.returncode != 0:
        return backfill_submission_queue_followup_result.returncode

    backfill_submission_queue_followup_resolution_command = (
        _build_backfill_submission_queue_followup_resolution_command(args)
    )
    backfill_submission_queue_followup_resolution_result = _run_command(
        backfill_submission_queue_followup_resolution_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution",
        backfill_submission_queue_followup_resolution_result,
    )
    if backfill_submission_queue_followup_resolution_result.returncode != 0:
        return backfill_submission_queue_followup_resolution_result.returncode

    backfill_submission_queue_followup_resolution_escalations_command = (
        _build_backfill_submission_queue_followup_resolution_escalations_command(args)
    )
    backfill_submission_queue_followup_resolution_escalations_result = _run_command(
        backfill_submission_queue_followup_resolution_escalations_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalations",
        backfill_submission_queue_followup_resolution_escalations_result,
    )
    if backfill_submission_queue_followup_resolution_escalations_result.returncode != 0:
        return backfill_submission_queue_followup_resolution_escalations_result.returncode

    backfill_submission_queue_followup_resolution_escalation_acknowledgements_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_acknowledgements_command(args)
    )
    backfill_submission_queue_followup_resolution_escalation_acknowledgements_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_acknowledgements_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-acknowledgements",
        backfill_submission_queue_followup_resolution_escalation_acknowledgements_result,
    )
    if backfill_submission_queue_followup_resolution_escalation_acknowledgements_result.returncode != 0:
        return backfill_submission_queue_followup_resolution_escalation_acknowledgements_result.returncode

    backfill_submission_queue_followup_resolution_escalation_throughput_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_throughput_command(args)
    )
    backfill_submission_queue_followup_resolution_escalation_throughput_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_throughput_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-throughput",
        backfill_submission_queue_followup_resolution_escalation_throughput_result,
    )
    if backfill_submission_queue_followup_resolution_escalation_throughput_result.returncode != 0:
        return backfill_submission_queue_followup_resolution_escalation_throughput_result.returncode

    backfill_submission_queue_followup_resolution_escalation_action_plan_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_command(args)
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan",
        backfill_submission_queue_followup_resolution_escalation_action_plan_result,
    )
    if backfill_submission_queue_followup_resolution_escalation_action_plan_result.returncode != 0:
        return backfill_submission_queue_followup_resolution_escalation_action_plan_result.returncode

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_command(args)
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_result,
    )
    if backfill_submission_queue_followup_resolution_escalation_action_plan_closure_result.returncode != 0:
        return backfill_submission_queue_followup_resolution_escalation_action_plan_closure_result.returncode

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_command(args)
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalations",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-ingestion",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalations",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalations",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_result.returncode
        )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_result.returncode
        )

    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command = (
        _build_backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command(
            args
        )
    )
    backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result = _run_command(
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_command
    )
    _print_command_output(
        "real-trial-backfill-submission-queue-followup-resolution-escalation-action-plan-closure-cadence-escalation-acknowledgement-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalation-closure-cadence-escalations",
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result,
    )
    if (
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result.returncode
        != 0
    ):
        return (
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_result.returncode
        )

    launch_gate_command = _build_launch_gate_command(
        args,
        trial_metrics_report=trial_metrics_output,
        controlled_trial_run_report=controlled_trial_run_report,
        launch_readiness_output=launch_readiness_output,
    )
    launch_gate_result = _run_command(launch_gate_command)
    _print_command_output("launch-readiness-gate", launch_gate_result)
    if launch_gate_result.returncode != 0:
        return launch_gate_result.returncode

    try:
        collection_report = _read_json(_resolve_required_output_path(args.collection_report_output, name="collection-report-output"))
        trial_metrics_report = _read_json(trial_metrics_output)
        launch_readiness_report = _read_json(launch_readiness_output)
        backfill_execution_report = _read_json(Path(args.backfill_execution_output).resolve())
        backfill_intake_actions_report = _read_json(Path(args.backfill_intake_actions_output).resolve())
        backfill_submission_templates_report = _read_json(Path(args.backfill_submission_templates_output).resolve())
        backfill_submission_consumption_report = _read_json(
            Path(args.backfill_submission_consumption_output).resolve()
        )
        backfill_submission_throughput_report = _read_json(
            Path(args.backfill_submission_throughput_output).resolve()
        )
        backfill_submission_queue_report = _read_json(
            Path(args.backfill_submission_queue_output).resolve()
        )
        backfill_submission_queue_completion_report = _read_json(
            Path(args.backfill_submission_queue_completion_output).resolve()
        )
        backfill_submission_queue_commitments_report = _read_json(
            Path(args.backfill_submission_queue_commitments_output).resolve()
        )
        backfill_submission_queue_commitment_closure_report = _read_json(
            Path(args.backfill_submission_queue_commitment_closure_output).resolve()
        )
        backfill_submission_queue_followup_report = _read_json(
            Path(args.backfill_submission_queue_followup_output).resolve()
        )
        backfill_submission_queue_followup_resolution_report = _read_json(
            Path(args.backfill_submission_queue_followup_resolution_output).resolve()
        )
        backfill_submission_queue_followup_resolution_escalations_report = _read_json(
            Path(args.backfill_submission_queue_followup_resolution_escalations_output).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_acknowledgements_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_acknowledgements_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_throughput_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_throughput_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_output
            ).resolve()
        )
        backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report = _read_json(
            Path(
                args.backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_output
            ).resolve()
        )
        backfill_handoff_report = _read_json(Path(args.backfill_handoff_output).resolve())
        backfill_handoff_escalations_report = _read_json(Path(args.backfill_handoff_escalations_output).resolve())
        manifest_preflight_report = _read_json(Path(args.manifest_preflight_report).resolve())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print("Real-trial launch evidence pipeline failed while reading reports: %s" % exc, file=sys.stderr)
        return 2

    try:
        evidence_pack = _build_evidence_pack(
            args=args,
            collection_report=collection_report,
            trial_metrics_report=trial_metrics_report,
            launch_readiness_report=launch_readiness_report,
            backfill_execution_report=backfill_execution_report,
            backfill_intake_actions_report=backfill_intake_actions_report,
            backfill_submission_templates_report=backfill_submission_templates_report,
            backfill_submission_consumption_report=backfill_submission_consumption_report,
            backfill_submission_throughput_report=backfill_submission_throughput_report,
            backfill_submission_queue_report=backfill_submission_queue_report,
            backfill_submission_queue_completion_report=backfill_submission_queue_completion_report,
            backfill_submission_queue_commitments_report=backfill_submission_queue_commitments_report,
            backfill_submission_queue_commitment_closure_report=backfill_submission_queue_commitment_closure_report,
            backfill_submission_queue_followup_report=backfill_submission_queue_followup_report,
            backfill_submission_queue_followup_resolution_report=backfill_submission_queue_followup_resolution_report,
            backfill_submission_queue_followup_resolution_escalations_report=backfill_submission_queue_followup_resolution_escalations_report,
            backfill_submission_queue_followup_resolution_escalation_acknowledgements_report=backfill_submission_queue_followup_resolution_escalation_acknowledgements_report,
            backfill_submission_queue_followup_resolution_escalation_throughput_report=backfill_submission_queue_followup_resolution_escalation_throughput_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_report=backfill_submission_queue_followup_resolution_escalation_action_plan_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalations_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_ingestion_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalations_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalations_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_report,
            backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report=backfill_submission_queue_followup_resolution_escalation_action_plan_closure_cadence_escalation_acknowledgement_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalation_closure_cadence_escalations_report,
            backfill_handoff_report=backfill_handoff_report,
            backfill_handoff_escalations_report=backfill_handoff_escalations_report,
            manifest_preflight_report=manifest_preflight_report,
            run_report_paths=run_report_paths,
            loop_manifest_paths=loop_manifest_paths,
        )
        _write_json(evidence_pack_output, evidence_pack)
        print("Real-trial launch evidence pack written: %s" % evidence_pack_output)
    except (OSError, ValueError) as exc:
        print("Real-trial launch evidence pipeline failed while writing evidence pack: %s" % exc, file=sys.stderr)
        return 2

    collection_alignment = collection_report.get("launch_gate_alignment", {})
    trial_metrics = trial_metrics_report.get("trial_metrics", {})
    launch_gate_evidence = trial_metrics.get("launch_gate_evidence", {}) if isinstance(trial_metrics, dict) else {}
    decision = str(launch_readiness_report.get("decision", "HOLD")).strip().upper() or "HOLD"
    failed_checks = launch_readiness_report.get("failed_checks", [])
    if not isinstance(failed_checks, list):
        failed_checks = []

    print(
        "Real-trial launch evidence pipeline decision=%s collection_status=%s real_eligible_complete=%s modalities=%s failed_checks=%s"
        % (
            decision,
            str(collection_alignment.get("program_status", "unknown")),
            int(launch_gate_evidence.get("complete_loop_count", 0) or 0),
            len(launch_gate_evidence.get("complete_modalities", []))
            if isinstance(launch_gate_evidence.get("complete_modalities", []), list)
            else 0,
            "none" if not failed_checks else ",".join(str(item) for item in failed_checks),
        )
    )
    if args.fail_on_hold and decision == "HOLD":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())






