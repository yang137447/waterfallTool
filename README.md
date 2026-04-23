# waterfallTool

`waterfallTool` 是一个 Blender 4.x 插件工程，用于从发射器生成瀑布流曲线，并基于曲线构建可编辑的 X-card 条带网格。

使用方式上，每个需要参与瀑布模拟的 Empty 都需要在 `Waterfall` 面板中显式启用为 `Waterfall Emitter`，并各自维护独立的发射参数、关联曲线与预览网格。
面板同时提供 Scene 级 `Global Properties` 和对象级 `Object Properties`，但两者职责完全分开：全局只管理统一物理环境、终止规则和 cutoff guide；对象只管理发射速度/方向、预览形态参数和对象关联字段。
面板分组支持折叠；预览相关开关统一收敛在 `Mesh Preview` 分组中，`Cutoff Guide` 单独作为截止辅助显示分组展示。
`Global Properties` 还提供自由模拟的终止规则：当轨迹速度低于 `Terminal Speed`，或点位世界高度低于 `Cutoff Height` 时，满足任一条件即停止继续生成后续点。
`Cutoff Height` 还会在视口中生成一个 Scene 级线框辅助框，支持 `XY Offset` 和 `XY Size`，用于直观查看截止平面的空间位置。
自由模拟在命中可支撑表面后，会沿表面切向重力继续流动，并结合接触摩擦逐步耗散速度；贴附阶段会做短距离贴面跟随、法线平滑，以还原真实水流附着并滑动的特性，减少三角边界上的“弹跳感”和人工转向的违和感，持续失去法线支撑后才恢复自由落体。
宽度控制也采用“基准宽度 + 相对倍率”的方式：基准宽度由曲线整体空间跨度和 `Base Width Ratio` 决定，路径中途绕远或碰撞滑行不会把宽度额外放大，`Start/End Scale` 只负责做相对缩放。
UV 目前只生成一套 `UV0`；其 `V` 方向会基于 `UV Base Speed` 相对当前流速做拉伸，速度越快，同等世界长度对应的 UV 距离越短。
网格密度采用新的双向控制：横向由 `Width Density` 控制宽度方向分片数；纵向由 `Longitudinal Step Length` 控制基础步长，并在曲率增大时按 `Curvature Min Angle` 自动减小有效步长。

## 适用对象

- 需要在 Blender 中快速搭建和迭代瀑布流体视觉的美术/TA
- 维护 Blender 插件逻辑、几何生成与测试的开发者

## 主要目录

- `addon/waterfall_tool/`: 插件主代码（注册、面板、属性、操作符、核心算法、Blender 适配层）
- `tests/core/`: 核心逻辑与操作符行为的 pytest 测试
- `scripts/`: 工具脚本（当前包含 Blender smoke 脚本）
- `docs/`: 项目事实文档

## 运行与验证入口

### 1) Python 测试

在可用的 Python 3 环境执行：

```bash
python -m pytest
```

说明：

- `pyproject.toml` 已将 `addon` 加入 pytest `pythonpath`
- 测试入口默认在 `tests/`

### 2) Blender Smoke 验证

使用 Blender 后台模式运行：

```bash
"C:\Software\blender-4.2.3-windows-x64\blender.exe" --background --factory-startup --python scripts/smoke_blender_addon.py
```

该脚本会执行注册、曲线模拟、预览重建、烘焙等关键链路并断言结果对象存在。

Blender 安装在 `C:\Software\blender-4.2.3-windows-x64` 时，插件安装目录为：

`C:\Software\blender-4.2.3-windows-x64\4.2\scripts\addons\`

### 3) 插件安装并激活（官方 Add-ons 流程）

当已有插件 ZIP 包时，可用 Blender 后台模式一键“安装 + 启用 + 保存用户偏好”：

```powershell
$blender = "C:\Software\blender-4.2.3-windows-x64\blender.exe"
$zip = "D:\YYBWorkSpace\GitHub\waterfallTool\waterfall_tool_addon.zip"
$expr = "import bpy; bpy.ops.preferences.addon_install(filepath=r'$zip', overwrite=True); bpy.ops.preferences.addon_enable(module='waterfall_tool'); bpy.ops.wm.save_userpref(); print('waterfall_tool installed+enabled')"
& $blender --background --factory-startup --python-expr $expr
```

## 入口文档

- AI 协作与执行约束：`AGENTS.md`
- 架构边界与模块职责：`docs/architecture.md`
- 验证梯度与测试策略：`docs/testing.md`
- 人机协作沉淀区说明：`docs/human-ai/README.md`
