"""
技能包存储管理模块

支持 Anthropic 官方格式的技能包存储：
- 每个技能包一个文件夹
- SKILL.md 定义技能包元数据和配置
- 可选的 scripts/ 文件夹存放脚本
- 可选的 references/ 文件夹存放参考资料
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SkillsStorage:
    """技能包文件系统存储管理器"""
    
    def __init__(self, storage_path: str = "./data/skills"):
        self.storage_path = Path(storage_path)
        self._skills_cache: Dict[str, Dict[str, Any]] = {}
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _load_skill_from_folder(self, folder_path: Path) -> Optional[Dict[str, Any]]:
        """从文件夹加载技能包"""
        skill_file = folder_path / "SKILL.md"
        
        if not skill_file.exists():
            logger.warning(f"技能包 {folder_path.name} 缺少 SKILL.md 文件")
            return None
        
        try:
            content = skill_file.read_text(encoding="utf-8")
            skill_data = self._parse_skill_md(content)
            
            # 添加基本元数据
            skill_data["id"] = folder_path.name
            skill_data["skill_path"] = str(folder_path)
            skill_data["enabled"] = skill_data.get("enabled", True)
            
            # 检查可选的脚本和参考资料
            scripts_dir = folder_path / "scripts"
            if scripts_dir.exists():
                skill_data["scripts"] = self._list_files_in_dir(scripts_dir)
            
            references_dir = folder_path / "references"
            if references_dir.exists():
                skill_data["references"] = self._list_files_in_dir(references_dir)
            
            return skill_data
            
        except Exception as e:
            logger.error(f"加载技能包 {folder_path.name} 失败: {e}")
            return None
    
    def _parse_skill_md(self, content: str) -> Dict[str, Any]:
        """解析 SKILL.md 内容"""
        skill_data = {
            "name": "",
            "description": "",
            "version": "1.0.0",
            "category": "未分类",
            "tags": [],
            "author": "",
            "enabled": True,
            "input_schema": {},
            "output_schema": {},
            "parameters": [],
            "examples": [],
            "capabilities": [],
            "configuration": {},
        }
        
        current_section = None
        section_content = []
        
        for line in content.split("\n"):
            # 检测章节标题
            if line.startswith("# ") and not skill_data["name"]:
                skill_data["name"] = line[2:].strip()
                continue
            elif line.startswith("## "):
                # 保存上一个章节的内容
                if current_section:
                    self._process_section(current_section, "\n".join(section_content), skill_data)
                
                current_section = line[3:].strip().lower()
                section_content = []
            else:
                section_content.append(line)
        
        # 处理最后一个章节
        if current_section:
            self._process_section(current_section, "\n".join(section_content), skill_data)
        
        return skill_data
    
    def _process_section(self, section: str, content: str, skill_data: Dict[str, Any]):
        """处理各个章节的内容"""
        content = content.strip()
        
        if "overview" in section:
            skill_data["description"] = content
        elif "capabilities" in section:
            # 解析能力列表
            capabilities = []
            for line in content.split("\n"):
                line = line.strip().lstrip("- ").lstrip("* ")
                if line:
                    capabilities.append(line)
            skill_data["capabilities"] = capabilities
        elif "input schema" in section:
            skill_data["input_schema"] = self._parse_json_block(content)
        elif "output schema" in section:
            skill_data["output_schema"] = self._parse_json_block(content)
        elif "examples" in section:
            skill_data["examples"] = self._parse_json_block(content)
            if not isinstance(skill_data["examples"], list):
                skill_data["examples"] = [skill_data["examples"]]
        elif "configuration" in section:
            # 解析配置信息
            for line in content.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower().replace("- ", "")
                    value = value.strip()
                    
                    if key == "version":
                        skill_data["version"] = value
                    elif key == "author":
                        skill_data["author"] = value
                    elif key == "category":
                        skill_data["category"] = value
                    elif key == "tags":
                        # 尝试解析 tags，处理多种格式
                        # 1. 如果 value 已经是列表，直接使用
                        if isinstance(value, list):
                            skill_data["tags"] = value
                        # 2. 尝试直接解析为 JSON 数组
                        elif value.strip().startswith("["):
                            try:
                                skill_data["tags"] = json.loads(value)
                            except (json.JSONDecodeError, ValueError):
                                # JSON 解析失败，按逗号分割
                                skill_data["tags"] = [t.strip().strip('"').strip("'") for t in value.split(",")]
                        # 3. 按逗号分割
                        else:
                            skill_data["tags"] = [t.strip().strip('"').strip("'") for t in value.split(",")]
    
    def _parse_json_block(self, content: str) -> Any:
        """解析 JSON 代码块"""
        import re
        
        # 查找 JSON 代码块
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if json_match:
            json_str = json_match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 尝试直接解析整个内容
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        return {}
    
    def _list_files_in_dir(self, dir_path: Path) -> List[Dict[str, str]]:
        """列出目录中的文件"""
        files = []
        for f in dir_path.rglob("*"):
            if f.is_file():
                files.append({
                    "name": f.name,
                    "path": str(f.relative_to(self.storage_path)),
                    "type": f.suffix[1:] if f.suffix else "file",
                })
        return files
    
    def load_all_skills(self) -> Dict[str, Dict[str, Any]]:
        """加载所有技能包"""
        skills = {}
        
        if not self.storage_path.exists():
            return skills
        
        for item in self.storage_path.iterdir():
            if item.is_dir():
                skill = self._load_skill_from_folder(item)
                if skill:
                    skills[skill["id"]] = skill
        
        self._skills_cache = skills
        return skills
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取指定技能包"""
        # 先检查缓存
        if skill_id in self._skills_cache:
            return self._skills_cache[skill_id]
        
        # 重新加载所有技能
        self.load_all_skills()
        return self._skills_cache.get(skill_id)
    
    def save_skill(self, skill_id: str, skill_data: Dict[str, Any]) -> bool:
        """保存技能包到文件系统"""
        try:
            skill_folder = self.storage_path / skill_id
            skill_folder.mkdir(parents=True, exist_ok=True)
            
            # 生成 SKILL.md 内容
            skill_md = self._generate_skill_md(skill_data)
            
            # 写入 SKILL.md
            skill_file = skill_folder / "SKILL.md"
            skill_file.write_text(skill_md, encoding="utf-8")
            
            # 更新缓存
            self._skills_cache[skill_id] = skill_data
            
            return True
        except Exception as e:
            logger.error(f"保存技能包 {skill_id} 失败: {e}")
            return False
    
    def _generate_skill_md(self, skill_data: Dict[str, Any]) -> str:
        """生成 SKILL.md 内容"""
        lines = []
        
        # 标题
        lines.append(f"# {skill_data.get('name', 'Unnamed Skill')}")
        lines.append("")
        
        # 概述
        if skill_data.get("description"):
            lines.append("## Overview")
            lines.append(skill_data["description"])
            lines.append("")
        
        # 能力
        if skill_data.get("capabilities"):
            lines.append("## Capabilities")
            for cap in skill_data["capabilities"]:
                lines.append(f"- {cap}")
            lines.append("")
        
        # 输入模式
        if skill_data.get("input_schema"):
            lines.append("## Input Schema")
            lines.append("```json")
            lines.append(json.dumps(skill_data["input_schema"], indent=2, ensure_ascii=False))
            lines.append("```")
            lines.append("")
        
        # 输出模式
        if skill_data.get("output_schema"):
            lines.append("## Output Schema")
            lines.append("```json")
            lines.append(json.dumps(skill_data["output_schema"], indent=2, ensure_ascii=False))
            lines.append("```")
            lines.append("")
        
        # 示例
        if skill_data.get("examples"):
            lines.append("## Examples")
            for example in skill_data["examples"]:
                lines.append("```json")
                lines.append(json.dumps(example, indent=2, ensure_ascii=False))
                lines.append("```")
            lines.append("")
        
        # 配置
        lines.append("## Configuration")
        lines.append(f"- Version: {skill_data.get('version', '1.0.0')}")
        if skill_data.get("author"):
            lines.append(f"- Author: {skill_data['author']}")
        lines.append(f"- Category: {skill_data.get('category', '未分类')}")
        if skill_data.get("tags"):
            lines.append(f"- Tags: {', '.join(skill_data['tags'])}")
        lines.append("")
        
        return "\n".join(lines)
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除技能包"""
        try:
            skill_folder = self.storage_path / skill_id
            if skill_folder.exists():
                import shutil
                shutil.rmtree(skill_folder)
            
            # 从缓存中移除
            if skill_id in self._skills_cache:
                del self._skills_cache[skill_id]
            
            return True
        except Exception as e:
            logger.error(f"删除技能包 {skill_id} 失败: {e}")
            return False
    
    def get_categories(self) -> Dict[str, int]:
        """获取所有分类及数量"""
        categories = {}
        
        for skill in self._skills_cache.values():
            cat = skill.get("category", "未分类")
            categories[cat] = categories.get(cat, 0) + 1
        
        return categories
    
    def reload(self):
        """重新加载所有技能包"""
        self._skills_cache.clear()
        self.load_all_skills()


# 全局技能存储实例
_skills_storage: Optional[SkillsStorage] = None


def get_skills_storage() -> SkillsStorage:
    """获取技能包存储实例"""
    global _skills_storage
    
    if _skills_storage is None:
        # 从配置获取存储路径
        try:
            from opspilot.utils.config import get_config
            config = get_config()
            storage_path = config.get("skills.storage_path", "./data/skills")
        except Exception:
            storage_path = "./data/skills"
        
        _skills_storage = SkillsStorage(storage_path)
        # 初始加载
        _skills_storage.load_all_skills()
    
    return _skills_storage
