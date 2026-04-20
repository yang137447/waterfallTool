# AGENTS.md

本文件面向在本仓库执行任务的 AI 协作者。目标是让实现、测试与文档始终对齐。

## 先读什么

开始任务前按顺序阅读：

1. `README.md`
2. `docs/architecture.md`
3. `docs/testing.md`

如果任务涉及过程记录、交接或方案讨论，再补读 `docs/human-ai/` 下相关文档。

## 仓库地图

- `addon/waterfall_tool/`: Blender 插件实现
- `tests/core/`: pytest 测试
- `scripts/`: Blender smoke 等脚本
- `docs/`: 事实文档
- `docs/human-ai/`: 过程性协作沉淀（默认不作为事实来源）

## 当前事实规则

- 插件入口由 `addon/waterfall_tool/__init__.py` 的 `register()/unregister()` 暴露。
- 类注册顺序和清单由 `addon/waterfall_tool/registration.py` 统一维护。
- 核心算法应位于 `addon/waterfall_tool/core/`，避免把纯逻辑写进 Blender API 交互层。
- `addon/waterfall_tool/adapters/` 负责 Blender 对象/数据访问，避免在 `core` 直接耦合 Blender 细节。
- 操作符工作流在 `addon/waterfall_tool/operators/`，由面板触发并调用核心能力。

## 默认执行模式

- 先定位根因，再决定修改层级；优先修正共享层和边界问题，不叠加局部补丁。
- 优先复用现有模块与入口，不复制规则、不并存新旧逻辑。
- 在不触发高风险条件时，连续执行到任务完成，不在中间里程碑无故停下。

## 明确禁止项

- 未经明确要求，不新增 fallback、compat、双写路径或临时并存逻辑。
- 不为绕过问题而静默降级、吞错或猜测性修复。
- 不伪造仓库中不存在的命令、流程、目录或契约。

## 必须停下来确认

出现以下任一情况，先说明风险和建议再等待确认：

- 需要改变公开行为或外部契约
- 需要修改插件对象命名规则、资源路径或加载约定
- 需要引入兼容层/迁移层或保留旧行为
- 需要高成本、大范围、长链路重写

## 实施与验证要求

- 文档变更：至少检查路径、命令名、交叉引用正确。
- 代码变更：按 `docs/testing.md` 的验证梯度选择最小充分验证。
- 验证失败：先区分环境问题与真实回归，再决定是否继续改代码。

## 文档更新规则

只要任务变更了以下任一项，必须同次更新对应文档：

- 目录结构
- 运行/测试命令
- 模块边界和事实来源
- 公开行为或协作约束

最低检查：

- `README.md`
- `AGENTS.md`
- `docs/architecture.md`
- `docs/testing.md`
