"""
配置加载器

职责：
- 加载 YAML 配置文件
- 支持环境变量覆盖
- 配置验证
- 提供全局配置访问点

使用方式：
    from opspilot.utils.config import get_config

    config = get_config()
    print(config.app.name)
"""
import os
from pathlib import Path
from typing import Optional, Any, Dict
from functools import lru_cache

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from opspilot.utils.exceptions import (
    ConfigError,
    ConfigFileNotFoundError,
    ConfigValidationError
)


# ==================== 配置模型定义 ====================

class AppConfig(BaseModel):
    """应用配置"""
    name: str = "opspilot"
    version: str = "0.1.0"
    debug: bool = False


class StateMachineConfig(BaseModel):
    """状态机配置"""
    initial_state: str = "INIT"
    max_retry: int = Field(default=3, ge=1, le=10)


class RedisConfig(BaseModel):
    """Redis 配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    prefix: str = "opspilot:"


class ChromaDBConfig(BaseModel):
    """ChromaDB 配置"""
    persist_directory: str = "./data/chromadb"
    collection_name: str = "opspilot_memory"


class MemoryConfig(BaseModel):
    """记忆系统配置"""
    redis: RedisConfig = Field(default_factory=RedisConfig)
    chromadb: ChromaDBConfig = Field(default_factory=ChromaDBConfig)


class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "sglang"
    model_name: str = ""
    api_base: str = ""
    api_key: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1)


class MCPServerConfig(BaseModel):
    """MCP Server 配置"""
    name: str
    command: str
    args: list = Field(default_factory=list)
    env: dict = Field(default_factory=dict)


class MCPConfig(BaseModel):
    """MCP 配置"""
    servers: list = Field(default_factory=list)


class APIConfig(BaseModel):
    """API 配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    cors_origins: list = Field(default_factory=lambda: ["*"])


class Settings(BaseSettings):
    """
    完整配置类

    支持从以下来源加载（优先级从高到低）：
    1. 环境变量（如 opspilot_APP__DEBUG=true）
    2. .env 文件
    3. config.yaml 文件
    4. 默认值
    """
    # 环境变量前缀
    model_config = {
        "env_prefix": "opspilot_",
        "env_nested_delimiter": "__",
        "case_sensitive": False
    }

    app: AppConfig = Field(default_factory=AppConfig)
    state_machine: StateMachineConfig = Field(default_factory=StateMachineConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    api: APIConfig = Field(default_factory=APIConfig)


# ==================== 配置加载器 ====================

class ConfigLoader:
    """
    配置加载器

    职责：
    - 查找配置文件
    - 加载 YAML 配置
    - 合并环境变量
    - 验证配置
    """

    DEFAULT_CONFIG_PATHS = [
        Path("config/config.yaml"),
        Path("config/config.yml"),
        Path("config.yaml"),
        Path("config.yml"),
    ]

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self._raw_config: Dict[str, Any] = {}

    def find_config_file(self) -> Optional[Path]:
        """查找配置文件"""
        if self.config_path and self.config_path.exists():
            return self.config_path

        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                return path

        return None

    def load_yaml(self, filepath: Path) -> Dict[str, Any]:
        """加载 YAML 文件"""
        if not filepath.exists():
            raise ConfigFileNotFoundError(str(filepath))

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f) or {}
            return content
        except yaml.YAMLError as e:
            raise ConfigValidationError(
                f"YAML 解析失败: {e}",
                field=str(filepath)
            )

    def load(self) -> Settings:
        """
        加载配置

        加载顺序：
        1. 加载 YAML 文件
        2. 创建 Settings 对象（自动合并环境变量）
        """
        config_file = self.find_config_file()

        if config_file:
            self._raw_config = self.load_yaml(config_file)

        # 使用 Pydantic Settings 自动合并环境变量
        return Settings(**self._raw_config)

    @property
    def raw_config(self) -> Dict[str, Any]:
        """获取原始配置字典"""
        return self._raw_config.copy()


# ==================== 全局配置访问 ====================

_config: Optional[Settings] = None
_config_path: Optional[str] = None


def init_config(config_path: Optional[str] = None, force_reload: bool = False) -> Settings:
    """
    初始化配置

    Args:
        config_path: 配置文件路径，为 None 时自动查找
        force_reload: 是否强制重新加载

    Returns:
        Settings: 配置对象
    """
    global _config, _config_path

    if _config is not None and not force_reload:
        return _config

    loader = ConfigLoader(config_path)
    _config = loader.load()
    _config_path = str(loader.find_config_file()) if loader.find_config_file() else None

    return _config


def get_config() -> Settings:
    """
    获取配置对象

    首次调用时自动初始化

    Returns:
        Settings: 配置对象
    """
    global _config

    if _config is None:
        _config = init_config()

    return _config


def get_config_path() -> Optional[str]:
    """获取当前使用的配置文件路径"""
    return _config_path


def reload_config() -> Settings:
    """重新加载配置"""
    return init_config(_config_path, force_reload=True)


# ==================== 便捷访问函数 ====================

def get_app_config() -> AppConfig:
    """获取应用配置"""
    return get_config().app


def get_state_machine_config() -> StateMachineConfig:
    """获取状态机配置"""
    return get_config().state_machine


def get_memory_config() -> MemoryConfig:
    """获取记忆系统配置"""
    return get_config().memory


def get_llm_config() -> LLMConfig:
    """获取 LLM 配置"""
    return get_config().llm


def get_mcp_config() -> MCPConfig:
    """获取 MCP 配置"""
    return get_config().mcp


def get_api_config() -> APIConfig:
    """获取 API 配置"""
    return get_config().api

