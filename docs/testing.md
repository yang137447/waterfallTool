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

**适用场景**：
- 升级或修改 Blender API 适配层（`adapters/`）。
- 变更插件属性定义（`properties.py`）。
- 发布新版本或提交 PR 前的最终完整确认。

## 推荐验证矩阵

- **改核心源码 (`core/`)**：至少跑 pytest。
- **改适配层 (`adapters/`) 或 UI (`panel.py`)**：至少跑 Blender Smoke Test。
- **发版或大范围重构**：两者皆需全部跑通。

## 测试踩坑收敛规则

- 对于 `bpy` 相关的报错，优先在 `adapters/` 中封装安全的访问方法，而不是在 `core/` 中写死 `try-except`。
- 如果 Blender 版本升级导致 API 废弃或时序行为变化，统一在 `adapters/` 中进行兼容性处理，并在 `AGENTS.md` 中记录新的坑点。
- 当集成测试偶发失败时，先区分是真实的逻辑回归，还是 Blender 内部 DepsGraph 未刷新的时序问题。
