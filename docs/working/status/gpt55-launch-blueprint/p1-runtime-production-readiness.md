# P1 Runtime 与生产链路施工方案

## 目标

修复 container smoke 失败，形成可声明生产链路的最低证据。该施工线不阻塞 P0 真实业务闭环收集，但阻塞任何“生产可用”宣称。

## 当前失败

依据 [Container Smoke Summary](../baselines/internal-dogfood-container-smoke-summary.md)：

| 阶段 | 结果 | 说明 |
| --- | --- | --- |
| Docker CLI | pass | Docker CLI 在 PATH 中 |
| Docker daemon | pass | Docker daemon 可连接 |
| image build | fail | 拉取 base image metadata 失败 |

判断：问题不是应用 health endpoint 的业务逻辑，而是构建环境无法获取或解析 base image 元数据。

## 施工路径 A：在线构建环境

适用于能访问外部 registry 或内部镜像代理的环境。

步骤：

1. 验证 Docker daemon。

```powershell
docker version
docker info
```

2. 验证 base image 拉取。

```powershell
docker pull python:3.11-slim
```

3. 若拉取失败，配置 Docker registry mirror 或内部代理。
4. 重新运行 container smoke。

```powershell
python scripts\container_smoke.py --image-tag omni-skill-pipeline:dogfood --container-name omni-skill-pipeline-smoke --health-url http://127.0.0.1:18000/healthz --print-json
```

5. 将新的 summary 写入 `docs/working/status/baselines/internal-dogfood-container-smoke-summary.md`。

## 施工路径 B：离线或受限网络

适用于 Docker daemon 可用，但不能访问外部 registry 的环境。

步骤：

1. 在可联网机器拉取并导出 base image。

```powershell
docker pull python:3.11-slim
docker save python:3.11-slim -o python-3.11-slim.tar
```

2. 在受限构建机导入。

```powershell
docker load -i python-3.11-slim.tar
```

3. 如项目 Dockerfile 使用 digest 或不同 tag，保持 base image tag 一致。
4. 重新运行 container smoke。

## Linux 发布验收

正式 production release 只能在 Linux 发布机上完成 Linux 脚本验收：

```bash
bash scripts/linux_release.sh
```

Windows 本地只能作为前置检查，不能替代 Linux 发布验收。

## K8s、Postgres、Vault/KMS 边界

当前诊断中，Docker 是生产链路最小阻塞；K8s、Postgres、Vault/KMS、自动 key rotation 属于更高等级生产化要求。

边界如下：

- 内部 dogfood：不要求 K8s、Postgres、Vault/KMS。
- Controlled Beta：可先不要求 K8s 和 Postgres，但必须明确部署边界。
- Production/GA：必须补齐 K8s 或等价部署方案、持久化存储方案、密钥管理和回滚方案。

## 完成定义

- `container_smoke.py` 输出 `PASS`。
- image build 不再卡在 base image metadata。
- health URL 返回成功。
- 若仍失败，summary 必须记录具体失败阶段、stderr 摘要、下一步动作。
- release note 不再把未通过的 container smoke 描述为生产可用。
