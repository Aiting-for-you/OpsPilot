"""
opspilot - 企业级运维智能体系统

架构设计（按文档要求）：
- AgentScope（决策层）：MsgHub、FSM状态机、Agent编排、博弈协调
- LangChain（执行层）：工具封装、RAG检索、记忆管理、Chain执行

存储：
- ChromaDB：向量存储（长期记忆）
- Redis：会话存储（短期记忆）
"""

__version__ = "0.1.0"

# 延迟导入，避免循环依赖
__all__ = [
    "__version__",
]

# 模块可用性检查
def check_dependencies():
    """检查依赖是否安装"""
    import importlib
    
    deps = {
        "langchain": "LangChain - 执行层框架",
        "langchain_chroma": "LangChain ChromaDB - 向量存储",
        "langchain_community": "LangChain Community - 工具和嵌入",
        "agentscope": "AgentScope - 决策层框架",
        "redis": "Redis - 会话存储",
    }
    
    available = {}
    for package, description in deps.items():
        try:
            importlib.import_module(package)
            available[package] = True
        except ImportError:
            available[package] = False
            print(f"警告: {package} 未安装 - {description}")
    
    return available


def get_framework_status():
    """获取框架状态"""
    try:
        from opspilot.memory import LANGCHAIN_AVAILABLE, REDIS_AVAILABLE
        from opspilot.agents import AGENTSCOPE_AVAILABLE
        from opspilot.tools import LANGCHAIN_EMBEDDINGS_AVAILABLE
        
        return {
            "langchain": LANGCHAIN_AVAILABLE,
            "agentscope": AGENTSCOPE_AVAILABLE,
            "redis": REDIS_AVAILABLE,
            "embeddings": LANGCHAIN_EMBEDDINGS_AVAILABLE,
        }
    except ImportError:
        return {
            "langchain": False,
            "agentscope": False,
            "redis": False,
            "embeddings": False,
        }

