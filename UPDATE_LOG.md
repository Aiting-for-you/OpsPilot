# 更新记录

## 2026-02-25

### README.md 优化

- 优化项目描述，改为「连接大语言模型与企业系统，实现运维自动化」
- 参考 LangChain/AgentScope 优秀开源项目规范
- 调整徽章顺序：Python/FastAPI/React/PostgreSQL/License + AgentScope/LangChain（版本号使用实际安装版本）
- 重新布局：
  - 标题 → 徽章 → 核心特性 → 主页预览（含截图）→ 架构设计 → 快速开始 → 文档 → 贡献
- 核心特性使用简洁表格，去除 AI 风格 Emoji
- 主页预览：添加截图 + 简单功能列表 + 引导查看完整功能模块（博弈定价、客服工单等）
- 架构图直接引用 docs/architecture/01_overall.md 完整内容
- 快速开始增加环境要求表格、安装步骤编号
- 文档简化为简单列表
- 贡献部分整合联系方式：cyx0414@outlook.com

### 新增文件

- docs/images/Homepage.png — 前端主页截图

### 技术栈版本（实际安装版本）

- Python: 3.10+
- FastAPI: 0.115.12
- Pydantic: 2.12.5
- SQLAlchemy: 2.0.40
- Redis: 6.4.0
- ChromaDB: 1.5.0
- AgentScope: 1.0.16
- LangChain: 0.3.25
- React: 19
