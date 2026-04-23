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
- Empty 只有在 `waterfall_emitter.enabled` 打开后才视为有效发射器；每个 Emitter 独立维护自身参数、曲线和预览对象关联。
- 若 Emitter 因复制带入旧 `flow_curve_name`，重算时会按归属校验并自动改用当前 Emitter 的独立曲线名，避免多个发射器复用同一条曲线对象。
- 对于由复制产生且引用旧曲线的 Emitter，重算时会继承源曲线的 `waterfall_curve` 预览参数模板，并复制源预览 Mesh 的材质槽到新预览 Mesh。
- Scene 级 `waterfall_global` 只承载全局物理环境、终止规则、cutoff guide 和面板折叠状态。
- 对象级 `waterfall_emitter` 仅保留 `enabled`、`speed`、`direction_axis` 与关联曲线名；对象级 `waterfall_curve` 保留预览形态、UV 和对象关联字段。
- 面板展示约定：预览相关开关统一放在 `Mesh Preview` 分组；`Cutoff Guide` 独立于终止逻辑展示；Global/Object 分组都支持折叠；不再提供全局同步按钮。
- 全局模拟支持 `Generate All Emitters` 批量重算：仅遍历 `enabled=True` 的 Empty 发射器，并保持每个发射器的曲线/预览关联独立。
- 自由模拟的终止条件由 `Scene.waterfall_global` 提供：速度低于 `terminal_speed` 或世界 Z 低于 `cutoff_height` 任一成立即终止；当前不作用于 `Physics Assisted`。
- 自由模拟附着阶段使用邻域探针构建宏观支撑面：`surface_flow_radius` 控制探测尺度，`surface_flow_samples` 控制探针数量，`surface_flow_relaxation` 控制点位向平滑支撑面的收敛强度，`surface_flow_inertia` 控制切向速度惯性保留。
- 碰撞采样仅接受 front-face 命中；背面命中应在 `adapters/blender_scene.py` 被过滤，避免薄片背面误附着。
- `cutoff_height` 还对应一个 Scene 级线框辅助对象，支持 `show_cutoff_guide`、`cutoff_offset_x/y` 与 `cutoff_size_x/y`，用于视口中显示终止平面。
- 宽度基准由绝对值 `base_width` 决定；这保证了无论轨迹是否因为碰撞或规则截断变短，发射起点的瀑布宽度都保持物理一致。
- `cross_ramp_length` 控制垂直 cross strip 的起始展开距离：起段先窄后宽，用于弱化崖口处突兀立片。
- 网格密度模型已切换为：`width_density` 控制横向分片；`longitudinal_step_length` 控制纵向基础步长；曲率越大时按 `curvature_min_angle_degrees` 自动减小纵向有效步长。

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
