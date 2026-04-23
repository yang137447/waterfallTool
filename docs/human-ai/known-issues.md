# 已知问题与避坑指南 (Known Issues & Gotchas)

本文档专门用于记录在 Blender 插件开发和测试过程中遇到的系统级坑点、崩溃原因以及相应的安全实践。

## Blender API 避坑与稳定实践

### 1. Depsgraph 回调中的安全限制与崩溃问题

**问题现象**：
在 `bpy.app.handlers.depsgraph_update_post` 回调中，如果直接触发可能会导致场景数据发生改变的操作（例如调用 `bpy.ops`，创建或删除网格物体、修改集合链接等），极易引发 Blender 发生硬崩溃（提示 `EXCEPTION_ACCESS_VIOLATION` 内存访问越界），或者引发依赖图的死循环。

**解决方案**：
绝对禁止在更新回调中直接执行上述敏感操作。应将需要处理的对象存入一个缓存列表或队列，并使用 `bpy.app.timers` 注册一个极短的延时执行任务（例如 `first_interval=0.01`）。这样可以安全地把对场景的重度修改推迟到依赖图更新完成、Blender 主线程处于空闲的安全时机。

```python
# 错误示范 (会引发崩溃)
def depsgraph_refresh(scene, depsgraph):
    for update in depsgraph.updates:
        obj = update.id
        if update.is_updated_transform:
            # 危险：直接在回调中重新生成网格物体
            generate_new_mesh(obj)

# 正确示范 (使用异步定时器)
_deferred_objects = []
_is_timer_registered = False

def _process_deferred_updates():
    global _is_timer_registered
    _is_timer_registered = False
    
    objects_to_process = list(_deferred_objects)
    _deferred_objects.clear()
    
    for obj in objects_to_process:
        if obj.name in bpy.data.objects:  # 确保对象依旧有效
            generate_new_mesh(obj)
            
    return None  # 返回 None 停止定时器

def depsgraph_refresh(scene, depsgraph):
    global _is_timer_registered
    has_new_updates = False
    
    for update in depsgraph.updates:
        obj = update.id
        if update.is_updated_transform:
            if obj not in _deferred_objects:
                _deferred_objects.append(obj)
                has_new_updates = True
                
    if has_new_updates and not _is_timer_registered:
        # 延迟到回调结束后安全执行
        bpy.app.timers.register(_process_deferred_updates, first_interval=0.01)
        _is_timer_registered = True
```
