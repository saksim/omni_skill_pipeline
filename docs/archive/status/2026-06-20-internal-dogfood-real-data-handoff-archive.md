# 内部 dogfood 与真实数据接入预案归档 2026-06-20

## 归档结论

本轮确认当前没有真实业务数据，因此 `v0.2.5-internal.1` 的发布口径限定为内部 dogfood 或内部玩具，不声明外部 Beta、GA、SaaS 或生产可用。

同时，本轮已经把后续真实数据接入方式落到当前手册层，后续只要拿到真实数据，就可以按固定目录、固定 manifest 槽位和固定验收命令接入项目。

## 已归档事实

- 原始真实数据本体应放在本地未入库目录：`data/real-inputs/<batch-id>/`。
- 仓库可提交的是脱敏后的真实闭环 manifest：`docs/working/status/baselines/real-trial-loop-collection/manifests/`。
- 10 个目标槽位和 4 个目标模态仍是外部 Beta/GA 的 P0 证据门禁。
- GL-64 已作为 GL-13 摄入前置门禁，pending 或 invalid 槽位不能进入 GL-13。
- 当前 launch gate 的主要业务 blocker 仍是 `trial_loop_volume_and_modality_coverage`。

## 已纳入当前发版的文档

- `docs/latest/operations/runbooks/real-data-intake-and-validation.md`
- `docs/latest/operations/runbooks/real-trial-loop-collection.md`
- `docs/working/status/gpt55-launch-blueprint/p0-real-loop-evidence.md`
- `docs/working/status/baselines/real-trial-loop-collection/manifests/README.md`
- `docs/releases/notes/v0.2.5-internal.1.md`

## 不属于本轮完成范围

- 真实业务数据本身。
- 外部 Beta readiness。
- GA/SaaS readiness。
- Docker、Postgres、K8s 生产链路闭环。
- Vault/KMS、自动 key rotation 或生产 secrets 管理。
- OCR hardening。

## 后续接手方式

后续工程师拿到真实数据后，先阅读：

```text
docs/latest/operations/runbooks/real-data-intake-and-validation.md
```

然后投递 10 个槽位 manifest，并执行：

```powershell
python -B scripts\gl64_real_loop_manifest_preflight.py --fail-on-invalid --fail-on-pending
python -B scripts\gl13_launch_evidence.py --loop-manifest-dir docs\working\status\baselines\real-trial-loop-collection\manifests --strict-loop-manifest-contract --require-manifest-preflight-ready --max-evidence-age-hours 0
python scripts\trial_metrics.py --manifest docs\working\status\baselines\real-trial-loop-collection\real-trial-loop-metrics-manifest.json --print-summary --fail-on-ga-blocker
python scripts\launch_gate.py --output - --summary-output - --max-evidence-age-hours 0 --print-json
```

## 一句话总结

本轮没有伪造真实数据，而是把当前版本定位为内部 dogfood，并把未来真实数据进入项目、放置位置、manifest 契约和验收命令固化为可执行中文手册。
