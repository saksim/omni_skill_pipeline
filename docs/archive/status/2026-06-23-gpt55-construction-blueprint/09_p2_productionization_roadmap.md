# P2：生产化路线——Docker、Postgres、K8s、密钥管理与产品入口

## 1. 背景

当前项目主要是内部 dogfood 级技能生产流水线。Docker、Postgres、K8s、生产级密钥管理、OCR 加固、Web/GUI/API Console 等仍属于后续增强范围。

这些能力不应阻塞 `v0.2.6-internal.3` 的自证闭环，但会阻塞真正的 GA 或规模化 SaaS。

## 2. 生产化分层

| 层级 | 目标 | 进入时机 |
|---|---|---|
| P2-A | Docker 单机可运行 | internal.3 后 |
| P2-B | Postgres/worker 持久化 | controlled beta 前后 |
| P2-C | K8s/对象存储/密钥管理 | beta 扩大前 |
| P2-D | 多租户/审计/计费/产品入口 | GA 前 |

## 3. Docker 路线

Docker 不只是 build 成功，还要 image build、container run、healthz、CLI/API smoke、日志采集、容器清理和文档复现。

验收命令：

```bash
python scripts/container_smoke.py
```

不能只跑：

```bash
python scripts/container_smoke.py --dry-run
```

完成定义：Dockerfile 可构建；image size 有记录；container health pass；API/CLI smoke pass；container logs 归档；CI 至少有 Docker smoke job。

## 4. Postgres / 持久化路线

当前代码已有 postgres/dual-write 相关结构，但生产级还需要：

| 能力 | 要求 |
|---|---|
| schema migration | 有迁移版本和回滚策略 |
| dual-write | 有一致性校验 |
| transaction | 关键写入原子性 |
| backup/restore | 有演练 |
| pg soak | 长时间运行稳定 |
| data retention | 与治理策略对齐 |

验收命令建议：

```bash
python scripts/pg_ga.py --print-json
python scripts/pg_soak.py --duration-minutes 60 --print-json
python scripts/bench_dual_write.py --print-json
```

## 5. K8s 路线

K8s 不应过早引入。进入条件：Docker real smoke 通过、API/worker 边界清楚、Postgres/对象存储配置清楚、Secret 管理方案明确。

K8s 最小清单：deployment、service、ingress、configmap、secret-ref、HPA、readinessProbe、livenessProbe。

验收：

```bash
kubectl apply --dry-run=server -f k8s/
kubectl rollout status deployment/omni-skill-pipeline
kubectl logs deployment/omni-skill-pipeline
```

## 6. 密钥管理路线

| Secret | 用途 | 存储方式 |
|---|---|---|
| OpenAI/API provider key | ASR/LLM/OCR provider | Secret Manager/Vault/KMS |
| DB password | Postgres | Secret Manager/Vault/KMS |
| Object storage credentials | source bundle | IAM role 优先 |
| Signing key | release artifact | KMS 或离线签名 |

禁止明文写入 repo、真实 key 写入 `.env.example`、把 source bundle URL 写成公开链接、在日志中打印 key。

## 7. 对象存储与 source bundle

真实 source bundle 不入 repo，生产环境建议放在 S3/GCS/Azure Blob 等对象存储。manifest 中只记录 storage ref、hash、redaction status、access policy、retention policy。

## 8. Web/API/GUI 产品入口

当前首要问题不是做 GUI，而是先闭环。若进入 beta，建议最小产品入口包括：source intake、job run、generated skill preview、human review、export/validate、evidence/manifest、launch gate dashboard。

CLI 仍应保留，因为 CLI 是最可靠的内部和 CI 入口，Web/GUI 不应替代 CLI 验收。

## 9. 可观测性

生产化需要记录 job duration/success/fail/retry、modality success rate、human review scores、release artifact build pass/fail、agent smoke pass/fail、redaction/secret access failures。

## 10. GA 前硬门槛

GA 前至少满足：真实用户/真实业务样本不少于 50 条；text/audio/image/video 均有质量统计；Docker 与 Postgres 稳定运行；Secret 管理完成；发布包签名/checksum/SBOM；回滚方案演练；审计日志可导出；数据删除/留存策略可执行；Beta 用户文档完整；严重失败模式有人工兜底。

## 11. 当前不建议做的事

在 P0/P1 未完成前，不建议大规模做 K8s、复杂 GUI、多租户计费、大量新 modality、性能极致优化、外部 Beta 宣传。当前真正瓶颈是“自证闭环和真实证据”，不是界面和规模。
