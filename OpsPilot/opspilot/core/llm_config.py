"""
LLM 配置管理模块

提供统一的 LLM 提供商配置管理：
- 支持主流模型：OpenAI、Azure OpenAI、Claude、通义千问、文心一言、智谱AI
- 支持自定义 API 端点
- 配置持久化与热更新
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import threading


class LLMProvider(str, Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    CLAUDE = "claude"
    QWEN = "qwen"           # 通义千问
    ERNIE = "ernie"         # 文心一言
    ZHIPU = "zhipu"         # 智谱AI
    DEEPSEEK = "deepseek"   # DeepSeek
    CUSTOM = "custom"       # 自定义


@dataclass
class ProviderConfig:
    """单个提供商配置"""
    provider: LLMProvider
    name: str                           # 显示名称
    api_key: str = ""                   # API Key
    api_base: str = ""                  # API 基础URL（可选，用于自定义端点）
    model_name: str = ""                # 模型名称
    default_model: str = ""             # 默认模型
    available_models: List[str] = field(default_factory=list)  # 可用模型列表
    
    # 模型参数
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    
    # 状态
    is_enabled: bool = False
    is_default: bool = False
    last_used: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（隐藏敏感信息）"""
        d = asdict(self)
        d["provider"] = self.provider.value
        # 隐藏部分 API Key
        if self.api_key:
            d["api_key_masked"] = self.api_key[:8] + "****" + self.api_key[-4:] if len(self.api_key) > 12 else "****"
        return d


# ==================== 预设提供商配置 ====================

PROVIDER_PRESETS: Dict[LLMProvider, Dict[str, Any]] = {
    LLMProvider.OPENAI: {
        "name": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "available_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o1-mini"],
    },
    LLMProvider.AZURE_OPENAI: {
        "name": "Azure OpenAI",
        "api_base": "",  # 需要用户填写
        "default_model": "gpt-4",
        "available_models": ["gpt-4", "gpt-4-32k", "gpt-35-turbo"],
    },
    LLMProvider.CLAUDE: {
        "name": "Anthropic Claude",
        "api_base": "https://api.anthropic.com/v1",
        "default_model": "claude-3-5-sonnet-20241022",
        "available_models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
    },
    LLMProvider.QWEN: {
        "name": "通义千问",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-max",
        "available_models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long"],
    },
    LLMProvider.ERNIE: {
        "name": "文心一言",
        "api_base": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
        "default_model": "ernie-4.0-8k",
        "available_models": ["ernie-4.0-8k", "ernie-4.0-turbo-8k", "ernie-3.5-8k"],
    },
    LLMProvider.ZHIPU: {
        "name": "智谱AI",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4",
        "available_models": ["glm-4", "glm-4-air", "glm-4-flash", "glm-4-plus"],
    },
    LLMProvider.DEEPSEEK: {
        "name": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "available_models": ["deepseek-chat", "deepseek-coder"],
    },
    LLMProvider.CUSTOM: {
        "name": "自定义模型",
        "api_base": "",
        "default_model": "",
        "available_models": [],
    },
}


class LLMConfigManager:
    """
    LLM 配置管理器
    
    功能：
    - 管理多个 LLM 提供商配置
    - 配置持久化存储
    - 热更新支持
    - 默认提供商管理
    """
    
    _instance: Optional[LLMConfigManager] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> LLMConfigManager:
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if self._initialized:
            return
        
        self._initialized = True
        self._providers: Dict[LLMProvider, ProviderConfig] = {}
        self._config_path: Optional[Path] = None
        self._on_change_callbacks: List[Callable[[], None]] = []
        
        # 初始化默认配置
        self._init_default_providers()
        
        # 从文件加载配置
        self._load_from_file()
    
    def _init_default_providers(self):
        """初始化默认提供商配置"""
        for provider, preset in PROVIDER_PRESETS.items():
            self._providers[provider] = ProviderConfig(
                provider=provider,
                name=preset["name"],
                api_base=preset["api_base"],
                default_model=preset["default_model"],
                available_models=preset["available_models"].copy(),
                is_enabled=False,
            )
    
    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        if self._config_path:
            return self._config_path
        
        # 尝试多个可能的路径
        possible_paths = [
            Path("data/llm_config.json"),
            Path("config/llm_config.json"),
            Path.home() / ".opspilot" / "llm_config.json",
        ]
        
        for path in possible_paths:
            if path.exists():
                self._config_path = path
                return path
        
        # 默认使用 data 目录
        default_path = Path("data/llm_config.json")
        default_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path = default_path
        return default_path
    
    def _load_from_file(self):
        """从文件加载配置"""
        config_path = self._get_config_path()
        
        if not config_path.exists():
            return
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for provider_str, config_data in data.get("providers", {}).items():
                try:
                    provider = LLMProvider(provider_str)
                    if provider in self._providers:
                        # 更新现有配置
                        existing = self._providers[provider]
                        existing.api_key = config_data.get("api_key", "")
                        existing.api_base = config_data.get("api_base", existing.api_base)
                        existing.model_name = config_data.get("model_name", existing.default_model)
                        existing.temperature = config_data.get("temperature", 0.7)
                        existing.max_tokens = config_data.get("max_tokens", 4096)
                        existing.top_p = config_data.get("top_p", 1.0)
                        existing.is_enabled = config_data.get("is_enabled", False)
                        existing.is_default = config_data.get("is_default", False)
                        existing.last_used = config_data.get("last_used")
                        
                        # 自定义模型支持额外模型列表
                        if provider == LLMProvider.CUSTOM:
                            custom_models = config_data.get("available_models", [])
                            if custom_models:
                                existing.available_models = custom_models
                except ValueError:
                    continue
                    
        except Exception as e:
            print(f"[LLMConfigManager] 加载配置失败: {e}")
    
    def _save_to_file(self):
        """保存配置到文件"""
        config_path = self._get_config_path()
        
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "providers": {}
            }
            
            for provider, config in self._providers.items():
                data["providers"][provider.value] = {
                    "api_key": config.api_key,
                    "api_base": config.api_base,
                    "model_name": config.model_name,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "top_p": config.top_p,
                    "is_enabled": config.is_enabled,
                    "is_default": config.is_default,
                    "last_used": config.last_used,
                }
                
                if provider == LLMProvider.CUSTOM:
                    data["providers"][provider.value]["available_models"] = config.available_models
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"[LLMConfigManager] 保存配置失败: {e}")
    
    def register_on_change(self, callback: Callable[[], None]):
        """注册配置变更回调"""
        self._on_change_callbacks.append(callback)
    
    def _notify_change(self):
        """通知配置变更"""
        for callback in self._on_change_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"[LLMConfigManager] 回调执行失败: {e}")
    
    # ==================== 公共 API ====================
    
    def get_provider_config(self, provider: LLMProvider) -> Optional[ProviderConfig]:
        """获取指定提供商配置"""
        return self._providers.get(provider)
    
    def get_all_providers(self) -> Dict[LLMProvider, ProviderConfig]:
        """获取所有提供商配置"""
        return self._providers.copy()
    
    def get_enabled_providers(self) -> List[ProviderConfig]:
        """获取已启用的提供商"""
        return [p for p in self._providers.values() if p.is_enabled]
    
    def get_default_provider(self) -> Optional[ProviderConfig]:
        """获取默认提供商"""
        for config in self._providers.values():
            if config.is_default and config.is_enabled:
                return config
        # 如果没有默认，返回第一个启用的
        enabled = self.get_enabled_providers()
        return enabled[0] if enabled else None
    
    def update_provider_config(
        self,
        provider: LLMProvider,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        is_enabled: Optional[bool] = None,
        is_default: Optional[bool] = None,
        available_models: Optional[List[str]] = None,
    ) -> ProviderConfig:
        """
        更新提供商配置
        
        Args:
            provider: 提供商类型
            api_key: API Key
            api_base: API 基础 URL
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            top_p: Top-p 参数
            is_enabled: 是否启用
            is_default: 是否设为默认
            available_models: 可用模型列表（仅自定义）
        
        Returns:
            更新后的配置
        """
        if provider not in self._providers:
            raise ValueError(f"未知的提供商: {provider}")
        
        config = self._providers[provider]
        
        # 更新字段
        if api_key is not None:
            config.api_key = api_key
        if api_base is not None:
            config.api_base = api_base
        if model_name is not None:
            config.model_name = model_name
        if temperature is not None:
            config.temperature = temperature
        if max_tokens is not None:
            config.max_tokens = max_tokens
        if top_p is not None:
            config.top_p = top_p
        if is_enabled is not None:
            config.is_enabled = is_enabled
        if available_models is not None:
            config.available_models = available_models
        
        # 处理默认提供商
        if is_default is True:
            # 取消其他默认
            for p, c in self._providers.items():
                c.is_default = (p == provider)
            config.is_default = True
        
        # 更新时间
        config.last_used = datetime.now().isoformat()
        
        # 保存并通知
        self._save_to_file()
        self._notify_change()
        
        return config
    
    def set_default_provider(self, provider: LLMProvider) -> bool:
        """设置默认提供商"""
        if provider not in self._providers:
            return False
        
        config = self._providers[provider]
        if not config.is_enabled:
            return False
        
        # 取消其他默认
        for c in self._providers.values():
            c.is_default = False
        
        config.is_default = True
        self._save_to_file()
        self._notify_change()
        
        return True
    
    def test_provider_connection(self, provider: LLMProvider) -> Dict[str, Any]:
        """
        测试提供商连接
        
        Returns:
            {"success": bool, "message": str, "latency_ms": int}
        """
        import time
        
        config = self._providers.get(provider)
        if not config:
            return {"success": False, "message": "提供商不存在"}
        
        if not config.api_key:
            return {"success": False, "message": "API Key 未配置"}
        
        if not config.api_base and provider != LLMProvider.CUSTOM:
            return {"success": False, "message": "API Base URL 未配置"}
        
        try:
            start_time = time.time()
            
            # 根据不同提供商进行测试
            if provider == LLMProvider.OPENAI:
                result = self._test_openai(config)
            elif provider == LLMProvider.CLAUDE:
                result = self._test_claude(config)
            elif provider == LLMProvider.QWEN:
                result = self._test_qwen(config)
            elif provider == LLMProvider.DEEPSEEK:
                result = self._test_deepseek(config)
            else:
                # 通用测试
                result = self._test_generic(config)
            
            latency_ms = int((time.time() - start_time) * 1000)
            result["latency_ms"] = latency_ms
            return result
            
        except Exception as e:
            return {"success": False, "message": f"连接测试失败: {str(e)}"}
    
    def _test_openai(self, config: ProviderConfig) -> Dict[str, Any]:
        """测试 OpenAI 连接"""
        import httpx
        
        url = f"{config.api_base.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {config.api_key}"}
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                
            if response.status_code == 200:
                return {"success": True, "message": "连接成功"}
            elif response.status_code == 401:
                return {"success": False, "message": "API Key 无效"}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _test_claude(self, config: ProviderConfig) -> Dict[str, Any]:
        """测试 Claude 连接"""
        # Claude API 测试
        return {"success": True, "message": "配置已保存，请通过实际调用验证"}
    
    def _test_qwen(self, config: ProviderConfig) -> Dict[str, Any]:
        """测试通义千问连接"""
        return {"success": True, "message": "配置已保存，请通过实际调用验证"}
    
    def _test_deepseek(self, config: ProviderConfig) -> Dict[str, Any]:
        """测试 DeepSeek 连接"""
        import httpx
        
        url = f"{config.api_base.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {config.api_key}"}
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                
            if response.status_code == 200:
                return {"success": True, "message": "连接成功"}
            elif response.status_code == 401:
                return {"success": False, "message": "API Key 无效"}
            else:
                return {"success": False, "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _test_generic(self, config: ProviderConfig) -> Dict[str, Any]:
        """通用连接测试"""
        return {"success": True, "message": "配置已保存，请通过实际调用验证"}
    
    def get_llm_client_config(self, provider: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """
        获取用于 LLM 客户端的配置
        
        Args:
            provider: 指定提供商，None 则使用默认
        
        Returns:
            客户端配置字典
        """
        if provider:
            config = self._providers.get(provider)
        else:
            config = self.get_default_provider()
        
        if not config:
            return {}
        
        return {
            "provider": config.provider.value,
            "api_key": config.api_key,
            "api_base": config.api_base,
            "model": config.model_name or config.default_model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
        }


# ==================== 全局访问函数 ====================

_manager: Optional[LLMConfigManager] = None


def get_llm_config_manager() -> LLMConfigManager:
    """获取 LLM 配置管理器单例"""
    global _manager
    if _manager is None:
        _manager = LLMConfigManager()
    return _manager


def get_llm_client_config(provider: Optional[str] = None) -> Dict[str, Any]:
    """
    获取 LLM 客户端配置（便捷函数）
    
    Args:
        provider: 提供商名称字符串，如 "openai", "claude" 等
    
    Returns:
        配置字典
    """
    manager = get_llm_config_manager()
    
    if provider:
        try:
            p = LLMProvider(provider)
            return manager.get_llm_client_config(p)
        except ValueError:
            pass
    
    return manager.get_llm_client_config()


def fetch_available_models(
    api_base: str,
    api_key: str,
    provider_type: str = "openai"
) -> Dict[str, Any]:
    """
    获取 API 端点支持的模型列表
    
    Args:
        api_base: API 基础 URL
        api_key: API Key
        provider_type: 提供商类型（用于选择不同的 API 格式）
    
    Returns:
        {"success": bool, "models": [...], "error": str}
    """
    import httpx
    
    if not api_base or not api_key:
        return {"success": False, "models": [], "error": "API Base URL 和 API Key 不能为空"}
    
    try:
        # 规范化 URL
        api_base = api_base.rstrip("/")
        
        with httpx.Client(timeout=15.0) as client:
            if provider_type in ["openai", "deepseek", "qwen", "custom"]:
                # OpenAI 兼容 API 格式
                url = f"{api_base}/models"
                headers = {"Authorization": f"Bearer {api_key}"}
                
                response = client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    
                    # 解析 OpenAI 格式的模型列表
                    for model in data.get("data", []):
                        model_id = model.get("id", "")
                        if model_id:
                            models.append({
                                "id": model_id,
                                "name": model.get("name", model_id),
                                "owned_by": model.get("owned_by", "unknown"),
                                "object": model.get("object", "model"),
                            })
                    
                    # 按名称排序
                    models.sort(key=lambda x: x["id"])
                    
                    return {"success": True, "models": models, "error": None}
                
                elif response.status_code == 401:
                    return {"success": False, "models": [], "error": "API Key 无效"}
                else:
                    return {"success": False, "models": [], "error": f"HTTP {response.status_code}: {response.text[:200]}"}
            
            else:
                # 其他提供商暂不支持自动获取
                return {
                    "success": False,
                    "models": [],
                    "error": f"暂不支持自动获取 {provider_type} 的模型列表，请手动输入模型名称"
                }
                
    except httpx.TimeoutException:
        return {"success": False, "models": [], "error": "连接超时，请检查网络或 API 地址"}
    except httpx.ConnectError:
        return {"success": False, "models": [], "error": "无法连接到 API 地址，请检查 URL 是否正确"}
    except Exception as e:
        return {"success": False, "models": [], "error": f"获取模型列表失败: {str(e)}"}


def batch_add_custom_models(
    provider: LLMProvider,
    api_key: str,
    api_base: str,
    models: List[str],
    temperature: float = 0.7,
    max_tokens: int = 4096,
    set_default: Optional[str] = None,
) -> Dict[str, Any]:
    """
    批量添加自定义模型配置
    
    Args:
        provider: 提供商类型
        api_key: API Key
        api_base: API 基础 URL
        models: 模型名称列表
        temperature: 温度参数
        max_tokens: 最大 Token 数
        set_default: 设置为默认的模型名称
    
    Returns:
        {"success": bool, "added_count": int, "default_model": str, "error": str}
    """
    manager = get_llm_config_manager()
    
    if not models:
        return {"success": False, "added_count": 0, "default_model": None, "error": "模型列表为空"}
    
    try:
        # 获取或创建提供商配置
        config = manager.get_provider_config(provider)
        if not config:
            return {"success": False, "added_count": 0, "default_model": None, "error": "提供商不存在"}
        
        # 更新配置
        manager.update_provider_config(
            provider=provider,
            api_key=api_key,
            api_base=api_base,
            available_models=models,
            model_name=models[0] if models else "",
            temperature=temperature,
            max_tokens=max_tokens,
            is_enabled=True,
            is_default=(set_default is not None),
        )
        
        # 设置默认模型
        default_model = None
        if set_default and set_default in models:
            default_model = set_default
            manager.update_provider_config(
                provider=provider,
                model_name=set_default,
                is_default=True,
            )
        elif models:
            default_model = models[0]
        
        return {
            "success": True,
            "added_count": len(models),
            "default_model": default_model,
            "error": None
        }
        
    except Exception as e:
        return {"success": False, "added_count": 0, "default_model": None, "error": str(e)}
