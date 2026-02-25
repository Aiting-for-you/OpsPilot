"""
内部工具模块

职责：
- 提供不需要外部系统调用的内置工具
- 数据格式化、计算、验证等功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


class InternalToolsServer(BaseToolServer):
    """
    内部工具 Server

    提供数据处理、格式转换、计算等内置功能
    """

    def __init__(self):
        super().__init__(
            name="internal-tools",
            description="内部工具集：数据格式化、计算、验证"
        )
        self._register_tools()

    def _register_tools(self):
        """注册所有内部工具"""

        # 格式化金额
        @self.register_tool(ToolSchema(
            name="format_currency",
            description="格式化金额显示",
            input_schema={
                "type": "object",
                "required": ["amount"],
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "金额数值"
                    },
                    "currency": {
                        "type": "string",
                        "description": "货币类型",
                        "default": "CNY"
                    }
                }
            }
        ))
        async def format_currency(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            amount = params.get("amount", 0)
            currency = params.get("currency", "CNY")

            # 格式化
            if currency == "CNY":
                formatted = f"¥{amount:,.2f}"
            elif currency == "USD":
                formatted = f"${amount:,.2f}"
            else:
                formatted = f"{amount:,.2f} {currency}"

            # 中文大写
            chinese = self._number_to_chinese(amount)

            return ToolResult.success({
                "formatted": formatted,
                "chinese": chinese,
                "amount": amount,
                "currency": currency
            })

        # 计算总价
        @self.register_tool(ToolSchema(
            name="calculate_total",
            description="计算订单总价",
            input_schema={
                "type": "object",
                "required": ["items"],
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "商品列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "price": {"type": "number"},
                                "quantity": {"type": "integer"}
                            }
                        }
                    },
                    "discount": {
                        "type": "number",
                        "description": "折扣比例（0-1）",
                        "default": 1.0
                    }
                }
            }
        ))
        async def calculate_total(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            items = params.get("items", [])
            discount = params.get("discount", 1.0)

            subtotal = 0
            item_details = []

            for item in items:
                price = item.get("price", 0)
                quantity = item.get("quantity", 1)
                item_total = price * quantity
                subtotal += item_total
                item_details.append({
                    "price": price,
                    "quantity": quantity,
                    "item_total": item_total
                })

            total = subtotal * discount
            discount_amount = subtotal - total

            return ToolResult.success({
                "subtotal": subtotal,
                "discount": discount,
                "discount_amount": discount_amount,
                "total": total,
                "item_count": len(items),
                "items": item_details
            })

        # 日期计算
        @self.register_tool(ToolSchema(
            name="calculate_date",
            description="日期计算",
            input_schema={
                "type": "object",
                "properties": {
                    "base_date": {
                        "type": "string",
                        "description": "基准日期（YYYY-MM-DD），默认今天"
                    },
                    "days_offset": {
                        "type": "integer",
                        "description": "天数偏移（正数为未来，负数为过去）"
                    },
                    "format": {
                        "type": "string",
                        "description": "输出格式",
                        "default": "%Y-%m-%d"
                    }
                }
            }
        ))
        async def calculate_date(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            from datetime import timedelta

            base_date_str = params.get("base_date")
            days_offset = params.get("days_offset", 0)
            fmt = params.get("format", "%Y-%m-%d")

            if base_date_str:
                base_date = datetime.strptime(base_date_str, "%Y-%m-%d")
            else:
                base_date = datetime.now()

            result_date = base_date + timedelta(days=days_offset)

            return ToolResult.success({
                "base_date": base_date.strftime(fmt),
                "result_date": result_date.strftime(fmt),
                "days_offset": days_offset,
                "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][result_date.weekday()]
            })

        # JSON 格式化
        @self.register_tool(ToolSchema(
            name="format_json",
            description="格式化 JSON 数据",
            input_schema={
                "type": "object",
                "required": ["data"],
                "properties": {
                    "data": {
                        "type": ["object", "array", "string"],
                        "description": "JSON 数据或字符串"
                    },
                    "indent": {
                        "type": "integer",
                        "description": "缩进空格数",
                        "default": 2
                    }
                }
            }
        ))
        async def format_json(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            data = params.get("data")
            indent = params.get("indent", 2)

            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError as e:
                    return ToolResult.error(
                        error=f"JSON 解析失败: {e}",
                        error_code="PARSE_ERROR"
                    )

            formatted = json.dumps(data, indent=indent, ensure_ascii=False)

            return ToolResult.success({
                "formatted": formatted,
                "data": data
            })

        # 数据验证
        @self.register_tool(ToolSchema(
            name="validate_data",
            description="验证数据格式",
            input_schema={
                "type": "object",
                "required": ["data", "validation_type"],
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "待验证数据"
                    },
                    "validation_type": {
                        "type": "string",
                        "description": "验证类型",
                        "enum": ["email", "phone", "id_card", "url", "date"]
                    }
                }
            }
        ))
        async def validate_data(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            data = params.get("data", "")
            validation_type = params.get("validation_type")

            patterns = {
                "email": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
                "phone": r"^1[3-9]\d{9}$",
                "id_card": r"^\d{17}[\dXx]$",
                "url": r"^https?://[\w\-.]+(:\d+)?(/[\w\-./?%&=]*)?$",
                "date": r"^\d{4}-\d{2}-\d{2}$"
            }

            pattern = patterns.get(validation_type)
            if not pattern:
                return ToolResult.error(
                    error=f"不支持的验证类型: {validation_type}",
                    error_code="INVALID_VALIDATION_TYPE"
                )

            is_valid = bool(re.match(pattern, data))

            return ToolResult.success({
                "is_valid": is_valid,
                "validation_type": validation_type,
                "data": data,
                "message": "验证通过" if is_valid else "验证失败"
            })

        # 合并数据
        @self.register_tool(ToolSchema(
            name="merge_data",
            description="合并多个数据源",
            input_schema={
                "type": "object",
                "required": ["sources"],
                "properties": {
                    "sources": {
                        "type": "array",
                        "description": "数据源列表",
                        "items": {
                            "type": "object"
                        }
                    },
                    "merge_strategy": {
                        "type": "string",
                        "description": "合并策略",
                        "enum": ["override", "keep_first", "deep_merge"],
                        "default": "override"
                    }
                }
            }
        ))
        async def merge_data(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            sources = params.get("sources", [])
            strategy = params.get("merge_strategy", "override")

            if not sources:
                return ToolResult.success({"merged": {}})

            result = {}

            if strategy == "override":
                for source in sources:
                    result.update(source)

            elif strategy == "keep_first":
                for source in sources:
                    for key, value in source.items():
                        if key not in result:
                            result[key] = value

            elif strategy == "deep_merge":
                result = self._deep_merge(sources)

            return ToolResult.success({
                "merged": result,
                "source_count": len(sources)
            })

    def _number_to_chinese(self, num: float) -> str:
        """数字转中文大写"""
        units = ["", "拾", "佰", "仟", "万", "拾", "佰", "仟", "亿"]
        digits = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]

        if num == 0:
            return "零元整"

        integer_part = int(num)
        decimal_part = round((num - integer_part) * 100)

        result = ""

        # 处理整数部分
        if integer_part > 0:
            i = 0
            while integer_part > 0:
                digit = integer_part % 10
                if digit != 0:
                    result = digits[digit] + units[i] + result
                elif result and not result.startswith("零"):
                    result = "零" + result
                integer_part //= 10
                i += 1
            result += "元"

        # 处理小数部分
        if decimal_part > 0:
            jiao = decimal_part // 10
            fen = decimal_part % 10
            if jiao > 0:
                result += digits[jiao] + "角"
            if fen > 0:
                result += digits[fen] + "分"
        else:
            result += "整"

        return result

    def _deep_merge(self, sources: List[Dict]) -> Dict:
        """深度合并"""
        result = {}
        for source in sources:
            for key, value in source.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge([result[key], value])
                else:
                    result[key] = value
        return result

    async def health_check(self) -> bool:
        """健康检查"""
        return True

