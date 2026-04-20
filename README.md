# waterfallTool

`waterfallTool` 是一个 Blender 4.x 插件工程，用于从发射器生成瀑布流曲线，并基于曲线构建可编辑的 X-card 条带网格。

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

## 入口文档

- AI 协作与执行约束：`AGENTS.md`
- 架构边界与模块职责：`docs/architecture.md`
- 验证梯度与测试策略：`docs/testing.md`
- 人机协作沉淀区说明：`docs/human-ai/README.md`
