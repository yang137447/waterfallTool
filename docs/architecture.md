# 架构总览

本文档描述 `waterfallTool` 插件工程的实际结构和单一事实来源。

## 顶层结构

- `addon/waterfall_tool/`: 插件主代码
- `tests/core/`: 核心逻辑测试（无 Blender 依赖环境或 Mock 环境）
- `scripts/`: 工具与自动化测试脚本
- `docs/`: 事实文档
- `docs/human-ai/`: 协作过程文档（非当前事实）

## 模块职责与接口契约

### `addon/waterfall_tool/core/` (核心算法)
- **职责**：纯几何计算、曲线采样、轨迹模拟、网格构建。
- **约束**：绝对禁止直接 import `bpy` 或强耦合 Blender 上下文。依赖于自定义的 `types.py` 等纯数据结构。
- **轨迹物理约定**：自由模拟命中可支撑表面后，会在附着状态下沿表面滑动，并叠加接触摩擦耗散；附着阶段允许短距离贴面跟随、对表面法线做平滑过渡，核心逻辑专注于贴附与重力/阻力的平面投影，不附加人为的转向干预，以还原真实水流的滑动与下落特性；只有持续失去表面接触或法线支撑力不足时才回退为自由落体。
- **宽度约定**：X-card 宽度不是直接使用绝对世界单位，而是先基于曲线整体空间跨度计算基准宽度，再乘以起止相对倍率；路径绕行、碰撞滑行等只改变轨迹形状，不应把基准宽度额外放大。
- **密度约定**：横向拓扑由 `width_density` 控制每条卡片横向分片数；纵向采样由 `longitudinal_step_length` 决定基础步长，并在局部曲率超过 `curvature_min_angle_degrees` 后进一步减小步长。
- **UV 约定**：网格只生成一套 `UV0`；`V` 方向基于路径长度并按 `UV Base Speed / 当前速度` 做相对拉伸，用单层 UV 直接表达流速差异。

### `addon/waterfall_tool/adapters/` (适配层)
- **职责**：Blender 数据结构（Curve, Mesh, Scene）与 Core 纯数据结构之间的转换。
- **约束**：所有针对 Blender 具体 API 的读写封装在此，对内提供干净的隔离接口。

### `addon/waterfall_tool/operators/` (操作符工作流)
- **职责**：响应用户操作（如 Simulate, Preview, Bake），编排 Adapter 与 Core 进行实际工作。
- **约束**：不做复杂的几何数学计算，仅负责调度和上下文环境检查。

### `addon/waterfall_tool/properties.py` & `panel.py` (表现层)
- **职责**：定义 Blender UI 面板和挂载在 Object 上的属性（PropertyGroup）。
- **补充约定**：Empty 只有在面板中显式启用后才视为 Waterfall Emitter；Emitter 参数、关联曲线名和预览网格名都按对象实例独立存储。
- **全局参数模型**：当前场景提供 `Scene.waterfall_global` 作为 `Global Properties`，仅承载统一物理环境、终止规则、cutoff guide 和折叠 UI 状态。
- **对象参数模型**：`waterfall_emitter` 仅保留 `enabled`、`speed`、`direction_axis` 和关联曲线名；`waterfall_curve` 保留预览形态、UV 与对象关联字段。
- **面板约定**：`Global Properties` 与 `Object Properties` 都支持折叠；不再提供 Global/Object 双向同步按钮。
- **终止规则**：自由模拟链路会读取 `Scene.waterfall_global` 的 `terminal_speed` 与 `cutoff_height`；满足“速度低于阈值”或“世界 Z 低于截止高度”任一条件即终止。该规则当前不作用于 `Physics Assisted` 重流。
- **截止可视化**：`Cutoff Height` 通过 Blender 适配层生成一个 Scene 级线框辅助对象，支持 `XY Offset` 与 `XY Size`，用于在视口中直观显示终止平面范围。

### `addon/waterfall_tool/registration.py` (注册机制)
- **职责**：统一管理所有需要向 Blender 注册的类，保证注册/注销顺序的稳定性。

## 运行时链路 (以生成曲线为例)

1. **输入**：用户在 3D 视图面板点击 "Generate / Re-simulate Curve"。
2. **路由**：触发 `WATERFALL_OT_simulate_curve` 操作符。
3. **适配**：操作符通过 `adapters` 读取当前 Emitter 的 Transform 和属性。
4. **计算**：调用 `core.trajectory.simulate_trajectory` 算出曲线控制点。
5. **渲染**：调用 `adapters.blender_curve.create_or_update_flow_curve` 在 Blender 中生成或更新 Curve 对象。

## 单一事实来源

- **插件入口注册顺序**：`registration.py` 中的 `CLASS_NAMES` 和 `_classes()`。
- **核心数据结构**：`core/types.py`
- **UI 属性定义**：`properties.py`
- **对外验证契约**：`tests/core/` 及 `scripts/smoke_blender_addon.py`
