"""
AgentScope Studio 集成

提供多智能体可视化监控能力。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class StudioConfig:
    """AgentScope Studio 配置"""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 5000
    
    # 存储配置
    save_dir: str = "./data/studio"
    
    # 功能开关
    enable_logging: bool = True
    enable_monitoring: bool = True
    enable_replay: bool = True
    
    # 其他 AgentScope 配置
    model_configs: list = field(default_factory=list)
    agent_configs: list = field(default_factory=list)
    
    def to_agentscope_config(self) -> Dict[str, Any]:
        """转换为 AgentScope 配置格式"""
        return {
            "studio": {
                "enable": self.enabled,
                "host": self.host,
                "port": self.port,
                "save_dir": self.save_dir,
            },
            "logging": {
                "enable": self.enable_logging,
                "level": "INFO",
            },
        }


class StudioIntegration:
    """
    AgentScope Studio 集成
    
    提供可视化监控和调试能力。
    
    示例:
        >>> studio = StudioIntegration(StudioConfig(enabled=True))
        >>> studio.start()
        >>> 
        >>> # Agent 执行会自动记录到 Studio
        >>> result = await agent.process(message)
        >>> 
        >>> # 获取监控数据
        >>> stats = studio.get_agent_stats()
    """
    
    def __init__(self, config: Optional[StudioConfig] = None):
        self.config = config or StudioConfig()
        self._initialized = False
        self._agentscope_available = False
        
        # 检查 AgentScope 是否可用
        try:
            import agentscope
            self._agentscope_available = True
        except ImportError:
            logger.warning(
                "AgentScope 未安装，Studio 功能不可用。"
                "请运行: pip install agentscope"
            )
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self._agentscope_available and self.config.enabled
    
    def start(self) -> bool:
        """
        启动 Studio
        
        Returns:
            bool: 是否成功启动
        """
        if not self.is_available():
            logger.info("Studio not available or disabled")
            return False
        
        if self._initialized:
            logger.info("Studio already initialized")
            return True
        
        try:
            import agentscope
            
            # 初始化 AgentScope with Studio
            agentscope.init(
                model_configs=self.config.model_configs,
                **self.config.to_agentscope_config()
            )
            
            self._initialized = True
            logger.info(
                f"AgentScope Studio started at "
                f"http://{self.config.host}:{self.config.port}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Studio: {e}")
            return False
    
    def stop(self) -> None:
        """停止 Studio"""
        self._initialized = False
        logger.info("Studio stopped")
    
    def get_dashboard_url(self) -> Optional[str]:
        """获取 Dashboard URL"""
        if self._initialized:
            return f"http://{self.config.host}:{self.config.port}"
        return None
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """获取 Agent 统计信息"""
        if not self._initialized:
            return {}
        
        try:
            import agentscope
            # 获取 AgentScope 的统计信息
            # 实际实现取决于 AgentScope API
            return {
                "initialized": self._initialized,
                "dashboard_url": self.get_dashboard_url(),
            }
        except Exception:
            return {"initialized": False}
    
    def get_conversation_history(self, limit: int = 100) -> list:
        """获取对话历史"""
        if not self._initialized:
            return []
        
        # 实际实现需要读取 AgentScope 的存储
        return []
    
    def export_logs(self, output_path: str) -> bool:
        """导出日志"""
        if not self._initialized:
            return False
        
        try:
            import shutil
            import os
            
            src_dir = self.config.save_dir
            if os.path.exists(src_dir):
                shutil.make_archive(output_path, 'zip', src_dir)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return False


# ============================================================================
# 全局 Studio 实例
# ============================================================================

_studio: Optional[StudioIntegration] = None


def get_studio() -> StudioIntegration:
    """获取全局 Studio 实例"""
    global _studio
    if _studio is None:
        _studio = StudioIntegration()
    return _studio


def init_studio(config: Optional[StudioConfig] = None) -> StudioIntegration:
    """
    初始化 Studio
    
    Args:
        config: Studio 配置
    
    Returns:
        StudioIntegration 实例
    """
    global _studio
    _studio = StudioIntegration(config)
    _studio.start()
    return _studio
