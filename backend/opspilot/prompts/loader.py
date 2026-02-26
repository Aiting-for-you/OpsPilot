"""
提示词加载器

职责：
- 从文件加载提示词
- 支持多种格式（YAML、JSON）
- 热重载支持
"""
from typing import Dict, Any, Optional
from pathlib import Path
import json

from opspilot.prompts.templates import PromptTemplate, PromptRegistry


class PromptLoader:
    """
    提示词加载器

    支持从文件系统加载提示词模板
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初始化

        Args:
            prompts_dir: 提示词目录路径
        """
        self._prompts_dir = Path(prompts_dir) if prompts_dir else None
        self._registry = PromptRegistry()

    def set_prompts_dir(self, directory: str) -> None:
        """设置提示词目录"""
        self._prompts_dir = Path(directory)

    def load_from_json(self, filepath: str) -> PromptTemplate:
        """
        从 JSON 文件加载提示词

        Args:
            filepath: 文件路径

        Returns:
            PromptTemplate: 加载的模板
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        template = PromptTemplate(
            name=data["name"],
            system_prompt=data.get("system_prompt", ""),
            user_prompt_template=data.get("user_prompt_template", ""),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
        )

        self._registry.register(template)
        return template

    def load_from_yaml(self, filepath: str) -> PromptTemplate:
        """
        从 YAML 文件加载提示词

        Args:
            filepath: 文件路径

        Returns:
            PromptTemplate: 加载的模板
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("需要安装 PyYAML: pip install pyyaml")

        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        template = PromptTemplate(
            name=data["name"],
            system_prompt=data.get("system_prompt", ""),
            user_prompt_template=data.get("user_prompt_template", ""),
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
        )

        self._registry.register(template)
        return template

    def load_all(self) -> int:
        """
        加载目录中所有提示词文件

        Returns:
            int: 加载的模板数量
        """
        if not self._prompts_dir or not self._prompts_dir.exists():
            return 0

        count = 0
        for filepath in self._prompts_dir.glob("*.json"):
            try:
                self.load_from_json(str(filepath))
                count += 1
            except Exception:
                pass

        for filepath in self._prompts_dir.glob("*.yaml"):
            try:
                self.load_from_yaml(str(filepath))
                count += 1
            except Exception:
                pass

        return count

    def reload(self) -> int:
        """重新加载所有提示词"""
        self._registry.clear()
        return self.load_all()

