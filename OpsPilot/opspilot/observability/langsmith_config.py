"""
LangSmith 集成

提供 LangChain 链路追踪能力。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class LangSmithConfig:
    """LangSmith 配置"""
    enabled: bool = True
    api_key: Optional[str] = None
    project: str = "opspilot"
    endpoint: str = "https://api.smith.langchain.com"
    
    # 追踪配置
    tracing_v2: bool = True
    hide_inputs: bool = False
    hide_outputs: bool = False
    hide_input_sequences: bool = True
    
    # 采样率
    sample_rate: float = 1.0  # 1.0 = 100%
    
    def apply_environment(self) -> None:
        """应用环境变量配置"""
        if self.enabled:
            # 启用 LangSmith 追踪
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            
            if self.api_key:
                os.environ["LANGCHAIN_API_KEY"] = self.api_key
            
            os.environ["LANGCHAIN_PROJECT"] = self.project
            
            if self.endpoint:
                os.environ["LANGCHAIN_ENDPOINT"] = self.endpoint
            
            logger.info(f"LangSmith enabled, project: {self.project}")
        else:
            # 禁用追踪
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            logger.info("LangSmith disabled")


class LangSmithIntegration:
    """
    LangSmith 集成
    
    提供链路追踪、调试和评估能力。
    
    示例:
        >>> langsmith = LangSmithIntegration(LangSmithConfig(
        ...     enabled=True,
        ...     api_key="your-api-key",
        ...     project="my-project",
        ... ))
        >>> langsmith.start()
        >>> 
        >>> # 所有 LangChain 调用会自动追踪
        >>> result = await chain.ainvoke("query")
    """
    
    def __init__(self, config: Optional[LangSmithConfig] = None):
        self.config = config or LangSmithConfig()
        self._initialized = False
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.config.enabled and (
            self.config.api_key is not None or 
            os.environ.get("LANGCHAIN_API_KEY") is not None
        )
    
    def start(self) -> bool:
        """
        启动 LangSmith 追踪
        
        Returns:
            bool: 是否成功启动
        """
        if not self.config.enabled:
            logger.info("LangSmith disabled")
            return False
        
        try:
            # 应用环境变量
            self.config.apply_environment()
            
            # 验证配置
            if not os.environ.get("LANGCHAIN_API_KEY"):
                logger.warning(
                    "LANGCHAIN_API_KEY not set. "
                    "Please set it in environment or config."
                )
                return False
            
            self._initialized = True
            logger.info(f"LangSmith started, project: {self.config.project}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start LangSmith: {e}")
            return False
    
    def stop(self) -> None:
        """停止追踪"""
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        self._initialized = False
        logger.info("LangSmith stopped")
    
    def get_project_url(self) -> Optional[str]:
        """获取项目 URL"""
        if self._initialized:
            return f"{self.config.endpoint}/projects/{self.config.project}"
        return None
    
    def get_run_url(self, run_id: str) -> Optional[str]:
        """获取运行 URL"""
        if self._initialized:
            return f"{self.config.endpoint}/projects/{self.config.project}/r/{run_id}"
        return None
    
    def create_dataset(
        self,
        name: str,
        description: str = "",
        examples: list = None,
    ) -> Optional[str]:
        """
        创建评估数据集
        
        Args:
            name: 数据集名称
            description: 描述
            examples: 示例列表
        
        Returns:
            数据集 ID 或 None
        """
        if not self._initialized:
            return None
        
        try:
            from langsmith import Client
            
            client = Client()
            dataset = client.create_dataset(
                dataset_name=name,
                description=description,
            )
            
            if examples:
                client.create_examples(
                    dataset_id=dataset.id,
                    examples=examples,
                )
            
            logger.info(f"Created dataset: {name}")
            return dataset.id
            
        except Exception as e:
            logger.error(f"Failed to create dataset: {e}")
            return None
    
    def log_feedback(
        self,
        run_id: str,
        key: str,
        score: float,
        comment: str = "",
    ) -> bool:
        """
        记录反馈
        
        Args:
            run_id: 运行 ID
            key: 反馈键
            score: 分数
            comment: 评论
        
        Returns:
            bool: 是否成功
        """
        if not self._initialized:
            return False
        
        try:
            from langsmith import Client
            
            client = Client()
            client.create_feedback(
                run_id=run_id,
                key=key,
                score=score,
                comment=comment,
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")
            return False


# ============================================================================
# 全局 LangSmith 实例
# ============================================================================

_langsmith: Optional[LangSmithIntegration] = None


def get_langsmith() -> LangSmithIntegration:
    """获取全局 LangSmith 实例"""
    global _langsmith
    if _langsmith is None:
        _langsmith = LangSmithIntegration()
    return _langsmith


def init_langsmith(config: Optional[LangSmithConfig] = None) -> LangSmithIntegration:
    """
    初始化 LangSmith
    
    Args:
        config: LangSmith 配置
    
    Returns:
        LangSmithIntegration 实例
    """
    global _langsmith
    _langsmith = LangSmithIntegration(config)
    _langsmith.start()
    return _langsmith
