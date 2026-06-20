# 发布说明

本目录保存 GitHub Release 工作流使用的人类可读发布说明。

当 release 改变操作人员或用户行为时，需要新增一个与 release tag 同名的 Markdown 文件：

```text
docs/releases/notes/<release_tag>.md
```

发布打包脚本会自动把匹配的发布说明插入生成的 `release-summary.md`。

## 已发布或待发布说明

- [v0.2.4-internal.1](v0.2.4-internal.1.md)：中文操作文档、文档分层核验、发布记录和归档记录补齐。
- [v0.2.3-internal.1](v0.2.3-internal.1.md)：内部 dogfood 本地 file artifact 加密加固。
- [v0.2.2-internal.1](v0.2.2-internal.1.md)：内部 dogfood API smoke 证据和 API version metadata 对齐。
- [v0.2.1-internal.1](v0.2.1-internal.1.md)：打包 contract 资源与 release consumer smoke 验证。
- [v0.2.0-internal.1](v0.2.0-internal.1.md)：正式 GitHub Release 机制和内部 release package 发布。
