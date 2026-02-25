# GUI 自动化设计

> **定位**：仅当 MCP 工具不可用时启用，作为降级补充方案。

---

## 1. 触发条件

GUI 自动化仅在下述情况下启用：

| 条件 | 说明 |
|------|------|
| **API 不存在** | 旧系统没有提供 API 接口 |
| **API 权限不足** | 当前角色无权调用该 API |
| **API 连续失败** | MCP 工具连续调用失败 3 次 |

---

## 2. 技术方案

### 2.1 技术选型

| 方案 | 优势 | 劣势 | 选择 |
|------|------|------|------|
| **UI-TARS** | 视觉定位，跨平台通用 | 需要模型推理 | ✅ 选择 |
| Playwright | 成熟稳定 | 依赖 DOM | ❌ |
| Selenium | 生态完善 | 维护成本高 | ❌ |

### 2.2 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│                    GUI 自动化执行流程                        │
└─────────────────────────────────────────────────────────────┘

[触发 GUI 模式]
      │
      ▼
┌─────────────┐
│  截图       │ → 获取当前页面视觉状态
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  感知       │ → UI-TARS 识别目标元素坐标
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  动作       │ → 模拟点击/输入/滚动
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  验证       │ → 截图对比确认结果
└──────┬──────┘
       │
       ▼
  [成功/失败]
```

---

## 3. 元素定位

### 3.1 多层容错定位

```python
class RobustElementLocator:
    def locate(self, description: str, screenshot: Image) -> Optional[Coordinates]:
        """多层容错定位"""
        
        # 层级 1：AI 模型精确识别
        coords = self.ai_model.locate(description, screenshot)
        if coords and self.verify(coords, screenshot):
            return coords
        
        # 层级 2：特征模糊匹配
        similar = self.feature_matcher.find_similar(description, screenshot, threshold=0.8)
        if similar:
            return similar[0].coords
        
        # 层级 3：OCR + 关键词
        text_regions = self.ocr.extract(screenshot)
        for region in text_regions:
            if description.lower() in region.text.lower():
                return region.center
        
        return None  # 定位失败
```

### 3.2 定位策略对比

| 策略 | 准确率 | 速度 | 适用场景 |
|------|--------|------|---------|
| AI 模型识别 | 95% | 慢 | 复杂界面 |
| 特征匹配 | 85% | 快 | 简单控件 |
| OCR 定位 | 70% | 中 | 文本按钮 |

---

## 4. 操作自验证

### 4.1 验证流程

```
[执行前截图] --> [执行操作] --> [执行后截图] --> [差异对比]
                                               │
                                       ┌───────┴───────┐
                                       ▼               ▼
                                   [变化符合预期]   [变化异常]
                                       │               │
                                       ▼               ▼
                                   [操作成功]     [回滚 + 重试]
```

### 4.2 验证策略

| 验证类型 | 说明 | 实现方式 |
|---------|------|---------|
| 视觉对比 | 前后截图差异 | SSIM 相似度 |
| 文本验证 | 关键文本出现 | OCR 提取 |
| 状态验证 | 页面状态变化 | DOM 快照 |

---

## 5. 故障处理

### 5.1 常见故障

| 故障类型 | 检测方式 | 恢复策略 |
|---------|---------|---------|
| 页面加载超时 | 10s 内无响应 | 刷新页面，重试 3 次 |
| 元素不存在 | 定位返回 None | 滚动页面，重新定位 |
| 弹窗遮挡 | 截图检测到弹窗 | 关闭弹窗，继续操作 |
| 网络中断 | HTTP 状态码异常 | 等待恢复，指数退避重试 |

### 5.2 人工介入

当 GUI 连续失败时，触发人工介入：

```python
if gui_failure_count >= 3:
    await notify_human(
        level="warning",
        message=f"GUI 操作连续失败 {gui_failure_count} 次",
        context=current_context,
        suggestion="请手动完成操作"
    )
```

---

## 6. GUI 工具列表

### 6.1 支持的系统

| 场景 | 目标系统 | 操作类型 | 优先级 |
|------|---------|---------|--------|
| ERP 录入 | 内部 ERP 网页 | 表单填写 | P0 |
| 报关申报 | 海关网站 | 表单填写 | P1 |
| 平台操作 | Amazon/Shopee | 数据查询 | P2 |

### 6.2 GUI 操作封装

```python
class GUIOperator:
    """GUI 操作封装"""
    
    async def fill_form(self, form_data: dict) -> bool:
        """填写表单"""
        for field, value in form_data.items():
            coords = await self.locate(field)
            if coords:
                await self.click(coords)
                await self.type(value)
        return await self.verify_submit()
    
    async def click_button(self, button_name: str) -> bool:
        """点击按钮"""
        coords = await self.locate(button_name)
        if coords:
            await self.click(coords)
            return await self.verify_action()
        return False
```

---

## 7. 落地约束

### 7.1 隐私保护

- 截图前自动遮蔽敏感信息（密码、个人 ID）
- 敏感操作不记录截图

### 7.2 人工确认

- GUI 操作在提交环节必须触发 `Human-in-the-loop` 确认
- 高风险操作需二次确认

### 7.3 审计日志

```json
{
  "gui_log_id": "gui-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "fill_form",
  "target_system": "ERP",
  "screenshots": ["before.png", "after.png"],
  "status": "success",
  "duration_ms": 2345
}
```

---

## 8. 影子模式 [面试应对]

> 注：以下内容为面试场景准备，实际开发按 MVP 优先。

### 8.1 影子模式定义

影子模式允许 Agent **模拟执行**而不真实操作，用于：
- 新模型上线前验证
- 新工具集成测试
- 持续性能监控

### 8.2 执行流程

```
[真实流量]
      │
      ▼
[流量复制器]
      │
      ├──→ [生产环境] (真实执行)
      │
      ├──→ [影子环境] (模拟执行)
      │
      └──→ [日志记录] (差异分析)
```

### 8.3 应用场景

| 阶段 | 用途 | 目标 |
|------|------|------|
| 新模型上线前 | 对比新旧模型表现 | 发现潜在问题 |
| 新工具集成 | 验证工具行为 | 确保符合预期 |
| 规则变更 | 评估变更影响 | 避免破坏性变更 |

