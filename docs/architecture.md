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

### `addon/waterfall_tool/adapters/` (适配层)
- **职责**：Blender 数据结构（Curve, Mesh, Scene）与 Core 纯数据结构之间的转换。
- **约束**：所有针对 Blender 具体 API 的读写封装在此，对内提供干净的隔离接口。

### `addon/waterfall_tool/operators/` (操作符工作流)
- **职责**：响应用户操作（如 Simulate, Preview, Bake），编排 Adapter 与 Core 进行实际工作。
- **约束**：不做复杂的几何数学计算，仅负责调度和上下文环境检查。

### `addon/waterfall_tool/properties.py` & `panel.py` (表现层)
- **职责**：定义 Blender UI 面板和挂载在 Object 上的属性（PropertyGroup）。

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
