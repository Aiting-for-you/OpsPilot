"""
工具描述压缩器 - Tool Compressor

压缩工具描述，减少token占用，同时保留关键信息。

核心功能：
1. 描述摘要
2. 参数简化
3. 模板压缩
4. Token估算
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from opspilot.tools.base import ToolSchema


class CompressionLevel(Enum):
    """压缩级别"""
    NONE = "none"          # 不压缩
    LIGHT = "light"        # 轻度压缩（保留主要信息）
    MODERATE = "moderate"  # 中度压缩（精简描述）
    AGGRESSIVE = "aggressive"  # 激进压缩（仅保留核心）


@dataclass
class CompressedTool:
    """压缩后的工具定义"""
    name: str
    action: str              # 简短动作描述
    params: List[str]        # 参数列表
    required_params: List[str]  # 必填参数
    returns: str             # 返回值描述
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI工具格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": f"{self.action}. 返回: {self.returns}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        p: {"type": "string", "description": p}
                        for p in self.params
                    },
                    "required": self.required_params,
                }
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "action": self.action,
            "params": self.params,
            "required_params": self.required_params,
            "returns": self.returns,
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": self.compression_ratio,
        }


class TokenEstimator:
    """Token估算器"""
    
    # 中文约1.5字符/token，英文约4字符/token
    CHARS_PER_TOKEN_ZH = 1.5
    CHARS_PER_TOKEN_EN = 4
    
    @classmethod
    def estimate(cls, text: str) -> int:
        """估算文本的token数"""
        if not text:
            return 0
        
        # 分离中英文
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        
        tokens = (
            chinese_chars / cls.CHARS_PER_TOKEN_ZH +
            other_chars / cls.CHARS_PER_TOKEN_EN
        )
        
        return int(tokens) + 1
    
    @classmethod
    def estimate_tool(cls, tool: ToolSchema) -> int:
        """估算工具定义的token数"""
        tokens = cls.estimate(tool.name)
        tokens += cls.estimate(tool.description)
        
        if tool.input_schema and isinstance(tool.input_schema, dict):
            props = tool.input_schema.get("properties", {})
            for prop_name, prop_info in props.items():
                tokens += cls.estimate(prop_name)
                if isinstance(prop_info, dict):
                    tokens += cls.estimate(prop_info.get("description", ""))
                    tokens += cls.estimate(str(prop_info.get("type", "")))
        
        return tokens


class ToolCompressor:
    """
    工具描述压缩器
    
    压缩策略：
    1. 描述摘要：提取核心动作
    2. 参数简化：仅保留名称和类型
    3. 返回值简化：简短描述
    4. 关键词提取：保留搜索关键词
    
    示例:
        >>> compressor = ToolCompressor()
        >>> compressed = compressor.compress(tool, level=CompressionLevel.MODERATE)
        >>> print(f"压缩率: {compressed.compression_ratio:.1%}")
    """
    
    # 常见动作动词映射
    ACTION_VERBS = {
        "query": "查询",
        "get": "获取",
        "fetch": "获取",
        "retrieve": "检索",
        "search": "搜索",
        "find": "查找",
        "create": "创建",
        "add": "添加",
        "insert": "插入",
        "update": "更新",
        "modify": "修改",
        "delete": "删除",
        "remove": "移除",
        "execute": "执行",
        "run": "运行",
        "calculate": "计算",
        "compute": "计算",
        "validate": "验证",
        "check": "检查",
        "verify": "确认",
        "format": "格式化",
        "parse": "解析",
        "convert": "转换",
    }
    
    # 中文动作词
    CN_ACTION_VERBS = {
        "查询": "查询",
        "获取": "获取",
        "搜索": "搜索",
        "查找": "查找",
        "创建": "创建",
        "添加": "添加",
        "更新": "更新",
        "修改": "修改",
        "删除": "删除",
        "执行": "执行",
        "计算": "计算",
        "验证": "验证",
        "检查": "检查",
        "格式化": "格式化",
        "解析": "解析",
        "转换": "转换",
    }
    
    def __init__(self):
        self.token_estimator = TokenEstimator()
    
    def compress(
        self,
        tool: ToolSchema,
        level: CompressionLevel = CompressionLevel.MODERATE,
    ) -> CompressedTool:
        """
        压缩工具描述
        
        Args:
            tool: 工具定义
            level: 压缩级别
        
        Returns:
            压缩后的工具定义
        """
        if level == CompressionLevel.NONE:
            return self._no_compression(tool)
        elif level == CompressionLevel.LIGHT:
            return self._light_compression(tool)
        elif level == CompressionLevel.MODERATE:
            return self._moderate_compression(tool)
        else:
            return self._aggressive_compression(tool)
    
    def _no_compression(self, tool: ToolSchema) -> CompressedTool:
        """不压缩"""
        original_tokens = self.token_estimator.estimate_tool(tool)
        
        return CompressedTool(
            name=tool.name,
            action=tool.description,
            params=self._extract_params(tool),
            required_params=self._extract_required(tool),
            returns="原始返回值",
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            compression_ratio=1.0,
        )
    
    def _light_compression(self, tool: ToolSchema) -> CompressedTool:
        """轻度压缩"""
        original_tokens = self.token_estimator.estimate_tool(tool)
        
        # 提取动作描述（取描述的第一句话）
        description = tool.description
        first_sentence = re.split(r'[。.!！\n]', description)[0]
        action = first_sentence[:100] if first_sentence else tool.name
        
        params = self._extract_params(tool)
        required = self._extract_required(tool)
        
        # 计算压缩后的 token 数量（使用相同的估计方法）
        compressed_description = f"{action} {', '.join(params[:3])}"
        compressed_tokens = self.token_estimator.estimate(compressed_description)
        
        return CompressedTool(
            name=tool.name,
            action=action,
            params=params,
            required_params=required,
            returns="返回结果",
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
        )
    
    def _moderate_compression(self, tool: ToolSchema) -> CompressedTool:
        """中度压缩"""
        original_tokens = self.token_estimator.estimate_tool(tool)
        
        # 提取动作动词
        action = self._extract_action(tool)
        
        # 简化参数
        params = self._extract_params(tool)
        required = self._extract_required(tool)
        
        # 简化返回值
        returns = self._extract_returns(tool)
        
        compressed_tokens = (
            self.token_estimator.estimate(action) +
            sum(self.token_estimator.estimate(p) for p in params) +
            self.token_estimator.estimate(returns) +
            15
        )
        
        return CompressedTool(
            name=tool.name,
            action=action,
            params=params,
            required_params=required,
            returns=returns,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
        )
    
    def _aggressive_compression(self, tool: ToolSchema) -> CompressedTool:
        """激进压缩"""
        original_tokens = self.token_estimator.estimate_tool(tool)
        
        # 仅保留核心信息
        action = self._extract_action(tool)[:30]
        params = self._extract_required(tool)  # 仅保留必填参数
        returns = "结果"
        
        compressed_tokens = (
            self.token_estimator.estimate(action) +
            sum(self.token_estimator.estimate(p) for p in params) +
            10
        )
        
        return CompressedTool(
            name=tool.name,
            action=action,
            params=params,
            required_params=params,
            returns=returns,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
        )
    
    def _extract_action(self, tool: ToolSchema) -> str:
        """提取动作描述"""
        name = tool.name.lower()
        description = tool.description
        
        # 从名称提取动词
        for en_verb, cn_verb in self.ACTION_VERBS.items():
            if en_verb in name:
                # 尝试从描述中提取对象
                object_match = re.search(
                    r'(?:供应商|订单|库存|政策|合规|用户|数据|信息)',
                    description
                )
                if object_match:
                    return f"{cn_verb}{object_match.group()}"
                return cn_verb
        
        # 从描述中提取动词
        for cn_verb in self.CN_ACTION_VERBS.values():
            if cn_verb in description:
                return cn_verb
        
        # 默认：取描述前20字
        return description[:20]
    
    def _extract_params(self, tool: ToolSchema) -> List[str]:
        """提取参数列表"""
        params = []
        
        if tool.input_schema and isinstance(tool.input_schema, dict):
            props = tool.input_schema.get("properties", {})
            params = list(props.keys())
        
        return params
    
    def _extract_required(self, tool: ToolSchema) -> List[str]:
        """提取必填参数"""
        if tool.input_schema and isinstance(tool.input_schema, dict):
            return tool.input_schema.get("required", [])
        return []
    
    def _extract_returns(self, tool: ToolSchema) -> str:
        """提取返回值描述"""
        # 从描述中查找返回值信息
        patterns = [
            r'返回[：:]\s*(.+?)(?:[。!！\n]|$)',
            r'返回值[：:]\s*(.+?)(?:[。!！\n]|$)',
            r'结果[：:]\s*(.+?)(?:[。!！\n]|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, tool.description)
            if match:
                return match.group(1)[:30]
        
        return "执行结果"
    
    def batch_compress(
        self,
        tools: List[ToolSchema],
        level: CompressionLevel = CompressionLevel.MODERATE,
    ) -> List[CompressedTool]:
        """批量压缩工具"""
        return [self.compress(tool, level) for tool in tools]
    
    def compress_for_context(
        self,
        tools: List[ToolSchema],
        max_tokens: int = 2000,
    ) -> List[CompressedTool]:
        """
        根据上下文预算自动选择压缩级别
        
        Args:
            tools: 工具列表
            max_tokens: 最大token数
        
        Returns:
            压缩后的工具列表
        """
        # 先尝试中度压缩
        compressed = self.batch_compress(tools, CompressionLevel.MODERATE)
        total_tokens = sum(c.compressed_tokens for c in compressed)
        
        if total_tokens <= max_tokens:
            return compressed
        
        # 尝试激进压缩
        compressed = self.batch_compress(tools, CompressionLevel.AGGRESSIVE)
        total_tokens = sum(c.compressed_tokens for c in compressed)
        
        if total_tokens <= max_tokens:
            return compressed
        
        # 按重要性截断
        compressed.sort(key=lambda c: c.compressed_tokens)
        result = []
        current_tokens = 0
        
        for c in compressed:
            if current_tokens + c.compressed_tokens <= max_tokens:
                result.append(c)
                current_tokens += c.compressed_tokens
            else:
                break
        
        return result


# 便捷函数
def compress_tools(
    tools: List[ToolSchema],
    level: CompressionLevel = CompressionLevel.MODERATE,
) -> List[CompressedTool]:
    """
    压缩工具列表的便捷函数
    
    Args:
        tools: 工具列表
        level: 压缩级别
    
    Returns:
        压缩后的工具列表
    """
    compressor = ToolCompressor()
    return compressor.batch_compress(tools, level)


def get_compression_stats(compressed: List[CompressedTool]) -> Dict[str, Any]:
    """获取压缩统计信息"""
    if not compressed:
        return {}
    
    total_original = sum(c.original_tokens for c in compressed)
    total_compressed = sum(c.compressed_tokens for c in compressed)
    
    return {
        "tool_count": len(compressed),
        "original_tokens": total_original,
        "compressed_tokens": total_compressed,
        "saved_tokens": total_original - total_compressed,
        "compression_ratio": total_compressed / total_original if total_original > 0 else 0,
    }

