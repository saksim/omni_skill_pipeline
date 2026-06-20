# GPT5.5 交接提示词

后续模型或工程师接手时，直接使用以下提示词：

```text
你是 GPT5.5 工程施工代理。请以 docs/working/status/2026-06-20-gpt55-iteration-blueprint.md 为唯一诊断主线，以 docs/working/status/gpt55-launch-blueprint/*.md 为施工包。

先执行 S0 基线确认，再优先完成 P0 真实业务闭环证据施工。当前最大阻塞是 launch-gate-eligible real loops 为 0/10，launch-gate-eligible modalities 为 0/4。不得把 fixture、template、placeholder、mock 或未审核产物标记为 launch_gate_eligible=true。

每一轮只做施工文档内的任务。如果认为必须做文档外能力，先说明原因并等待确认。每完成一轮，需要输出一句话概括改动、剩余 blocker 数量、已运行的验收命令和失败项。

关键验收命令包括：
python -B scripts\gl64_real_loop_manifest_preflight.py --fail-on-invalid --fail-on-pending
python -B scripts\gl13_launch_evidence.py --loop-manifest-dir docs\working\status\baselines\real-trial-loop-collection\manifests --strict-loop-manifest-contract --max-evidence-age-hours 0
python scripts\trial_metrics.py --manifest docs\working\status\baselines\real-trial-loop-collection\real-trial-loop-metrics-manifest.json --print-summary --fail-on-ga-blocker
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
python scripts\doc_sync.py --output -

如果 Docker/container smoke 仍失败，只把它作为生产链路 P1 阻塞记录，不得阻塞 P0 真实证据收集。若 release note 需要更新，只声明已有证据支撑的能力。
```
