# Real Trial Loop Manifests

Place operator-collected real loop manifest JSON files in this directory before running GL-13 batch intake.

This directory is intentionally empty in source control except this README. The release artifact pipeline does not generate real Beta evidence here. A valid manifest must be a JSON object with a top-level `loops` list. Each launch-gate-eligible row must carry real evidence labels and trace fields such as `evidence_origin=real`, `launch_gate_eligible=true`, `source_system`, `source_reference`, `collected_at_utc`, `review_task_id`, `reviewed_by`, and `reviewed_at_utc`.

Use `real-trial-loop-metrics-manifest.template.json` in the parent directory as the contract reference.
