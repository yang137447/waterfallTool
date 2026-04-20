# Human-AI 协作区说明

`docs/human-ai/` 用于沉淀人类与 AI 协作过程中的背景、方案、权衡、待确认事项、handoff、progress 和共享说明文档。

默认情况下，这个目录不属于当前事实来源。  
除非某份文档明确写明自己已升格为事实，否则后续任务仍以 `README.md`、`docs/architecture.md`、`docs/testing.md` 和其他正式事实文档为准。

## 适合放什么

- 设计稿 (`YYYY-MM-DD-<topic>-design.md`)
- 方案比较
- 执行计划
- progress / handoff 文档 (`YYYY-MM-DD-<topic>-handoff.md`)
- 任务背景补充

## 不适合放什么

- 当前已经稳定成立、应作为仓库事实的规则（请移步 `AGENTS.md` 或 `docs/architecture.md`）
- 需要被所有实现与 review 默认遵守的正式契约
- 运行时代码或可直接调用的自动化脚本

如果某份协作文档已经稳定成为当前事实，应把它迁移或升格到 `docs/` 的正式事实文档中，并在原文档里注明去向。
