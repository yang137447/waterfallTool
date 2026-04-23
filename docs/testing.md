# 测试与验证

本文档描述 `waterfallTool` 插件当前常用的验证命令，以及什么时候该跑哪一层。

## 验证梯度

1. `python -m pytest` (核心与逻辑单测)
2. `Blender Smoke Test` (端到端集成验证)

## 每条命令做什么

### 1. Python pytest 测试

**用途**：
- 验证纯核心算法（`core/`）的正确性。
- 验证操作符（`operators/`）的调度逻辑（基于 Mock 或 Monkeypatch）。

**命令**：
```bash
python -m pytest
```

**适用场景**：
- 修改核心几何算法、轨迹模拟或网格生成逻辑。
- 优点是速度极快，且无须安装和启动 Blender。

### 2. Blender Smoke 验证

**用途**：
- 在真实的 Blender 实例中，跑通“注册插件 -> 选定发射器 -> 模拟曲线 -> 生成预览 -> 烘焙网格 -> 卸载插件”的完整用户链路。

**命令**：
```bash
"C:\Software\blender-4.2.3-windows-x64\blender.exe" --background --factory-startup --python scripts/smoke_blender_addon.py
```

Blender 安装在 `C:\Software\blender-4.2.3-windows-x64` 时，插件安装目录为：

`C:\Software\blender-4.2.3-windows-x64\4.2\scripts\addons\`

**适用场景**：
- 升级或修改 Blender API 适配层（`adapters/`）。
- 变更插件属性定义（`properties.py`）。
- 发布新版本或提交 PR 前的最终完整确认。

## 推荐验证矩阵

- **改核心源码 (`core/`)**：至少跑 pytest。
- **改适配层 (`adapters/`) 或 UI (`panel.py`)**：至少跑 Blender Smoke Test。
- **改 Emitter 识别、对象属性或多对象隔离逻辑**：至少跑 pytest 和 Blender Smoke Test，并确认两个 Empty 可分别启用、分别生成、互不串扰。
- **改多发射器批量生成逻辑**：至少跑 pytest 和 Blender Smoke Test，并确认 `Generate All Emitters` 只处理启用的 Empty，且不会覆盖其他发射器的曲线关联。
- **改复制发射器继承逻辑**：至少跑 pytest，并确认复制后的 Emitter 会继承源曲线预览参数与预览 Mesh 材质槽，同时仍保持曲线对象独立。
- **改 Global/Object 参数归属或面板结构**：至少跑 pytest 和 Blender Smoke Test，并确认全局物理参数与对象发射/预览参数已彻底分离。
- **改面板分组或折叠逻辑**：至少执行 Blender Smoke Test，并人工检查 `Global Properties`、`Object Properties`、`Mesh Preview`、`Termination`、`Cutoff Guide` 的归属和折叠状态是否清晰。
- **改终止规则或自由模拟停止条件**：至少跑 `test_trajectory.py`，确认 `Terminal Speed` 与 `Cutoff Height` 的任一终止逻辑符合预期，且不影响 `Physics Assisted`。
- **改碰撞响应或附着表面运动**：至少跑 `test_trajectory.py`，确认命中表面后会沿切向继续运动、速度会因接触摩擦合理衰减，小型采样缝隙不会立即离面弹起，附着流向会保留主流惯性并避免单步硬转折，且持续失去接触后能恢复自由落体。
- **改碰撞命中过滤（正/背面）**：至少跑 `test_blender_adapters.py`，确认 back-face 命中被忽略，front-face 命中仍可正常返回碰撞点和法线。
- **改 Cutoff Height 视口辅助显示**：至少跑相关单测并执行 Blender Smoke Test，确认线框高度、XY 偏移和尺寸参数都能生效。
- **改宽度语义或网格尺度逻辑**：至少跑 `test_curve_sampling.py` 和 `test_mesh_builder.py`，确认基准宽度、相对倍率，以及路径绕行时宽度不被弧长异常放大都按预期生效。
- **改 cross strip 起始展开逻辑**：至少跑 `test_mesh_builder.py`，确认垂直条带在起始段按 `cross_ramp_length` 逐步加宽，而非第一排即满宽。
- **改网格密度模型**：至少跑 `test_curve_sampling.py` 和 `test_mesh_builder.py`，确认 `Width Density`、`Longitudinal Step Length` 与 `Curvature Min Angle` 会正确影响横向分片和纵向采样。
- **改 UV 语义或速度驱动拉伸逻辑**：至少跑 `test_mesh_builder.py` 和 Blender Smoke Test，确认只生成单层 UV 且 `UV Base Speed` 会正确影响 `V` 方向拉伸。
- **发版或大范围重构**：两者皆需全部跑通。

## 测试踩坑收敛规则

- 对于 `bpy` 相关的报错，优先在 `adapters/` 中封装安全的访问方法，而不是在 `core/` 中写死 `try-except`。
- 如果 Blender 版本升级导致 API 废弃或时序行为变化，统一在 `adapters/` 中进行兼容性处理，并在 `docs/human-ai/known-issues.md` 中记录新的坑点。
- 当集成测试偶发失败时，先区分是真实的逻辑回归，还是 Blender 内部 DepsGraph 未刷新的时序问题。
