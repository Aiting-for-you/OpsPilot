"""
文件操作工具模块

提供文件读写、日志解析等 MCP 工具封装。

特性：
- 安全文件读写
- 日志解析
- 文件搜索
- 格式转换
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    name: str
    size: int
    is_dir: bool
    modified_time: float
    created_time: float
    permissions: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "is_dir": self.is_dir,
            "modified_time": datetime.fromtimestamp(self.modified_time).isoformat(),
            "created_time": datetime.fromtimestamp(self.created_time).isoformat(),
            "permissions": self.permissions,
        }


@dataclass
class FileOperationResult:
    """文件操作结果"""
    success: bool
    path: str
    operation: str
    data: Any = None
    error: str = ""
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "path": self.path,
            "operation": self.operation,
            "data": self.data,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class FileOperations:
    """
    文件操作工具
    
    提供安全的文件读写能力。
    """
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {
        ".txt", ".log", ".json", ".yaml", ".yml",
        ".csv", ".xml", ".html", ".md", ".rst",
        ".py", ".js", ".ts", ".java", ".go", ".rs",
        ".sh", ".bash", ".zsh",
        ".conf", ".cfg", ".ini", ".env",
        ".toml", ".properties",
    }
    
    # 禁止访问的路径
    BLOCKED_PATHS = [
        "/etc/shadow",
        "/etc/passwd",
        "/root/.ssh",
        "~/.ssh",
        ".env",  # 敏感配置文件
    ]
    
    # 最大文件大小 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
    
    def _resolve_path(self, path: str) -> Path:
        """解析并验证路径"""
        # 处理相对路径
        if not os.path.isabs(path):
            full_path = (self.base_path / path).resolve()
        else:
            full_path = Path(path).resolve()
        
        # 检查是否在基础路径下（可选安全限制）
        # try:
        #     full_path.relative_to(self.base_path)
        # except ValueError:
        #     raise PermissionError(f"路径超出允许范围: {path}")
        
        return full_path
    
    def _is_allowed(self, path: Path) -> tuple[bool, str]:
        """检查文件是否允许访问"""
        # 检查禁止路径
        path_str = str(path)
        for blocked in self.BLOCKED_PATHS:
            if blocked in path_str:
                return False, f"禁止访问的路径: {blocked}"
        
        # 检查扩展名
        ext = path.suffix.lower()
        if ext and ext not in self.ALLOWED_EXTENSIONS:
            return False, f"不允许的文件类型: {ext}"
        
        # 检查文件大小
        if path.exists() and path.is_file():
            size = path.stat().st_size
            if size > self.MAX_FILE_SIZE:
                return False, f"文件过大: {size} > {self.MAX_FILE_SIZE}"
        
        return True, ""
    
    async def read_file(
        self,
        path: str,
        encoding: str = "utf-8",
        start_line: int = 0,
        end_line: Optional[int] = None,
    ) -> FileOperationResult:
        """
        读取文件
        
        Args:
            path: 文件路径
            encoding: 编码
            start_line: 起始行
            end_line: 结束行
        """
        start_time = time.time()
        
        try:
            full_path = self._resolve_path(path)
            
            # 检查权限
            is_allowed, error = self._is_allowed(full_path)
            if not is_allowed:
                return FileOperationResult(
                    success=False,
                    path=path,
                    operation="read",
                    error=error,
                )
            
            if not full_path.exists():
                return FileOperationResult(
                    success=False,
                    path=path,
                    operation="read",
                    error="文件不存在",
                )
            
            if not full_path.is_file():
                return FileOperationResult(
                    success=False,
                    path=path,
                    operation="read",
                    error="不是文件",
                )
            
            # 读取文件
            with open(full_path, "r", encoding=encoding) as f:
                lines = f.readlines()
            
            # 行范围
            if end_line is None:
                end_line = len(lines)
            lines = lines[start_line:end_line]
            
            return FileOperationResult(
                success=True,
                path=path,
                operation="read",
                data={
                    "content": "".join(lines),
                    "total_lines": len(lines),
                    "start_line": start_line,
                    "end_line": start_line + len(lines),
                },
                duration_ms=(time.time() - start_time) * 1000,
            )
        
        except Exception as e:
            return FileOperationResult(
                success=False,
                path=path,
                operation="read",
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )
    
    async def write_file(
        self,
        path: str,
        content: str,
        mode: str = "write",
        encoding: str = "utf-8",
    ) -> FileOperationResult:
        """
        写入文件
        
        Args:
            path: 文件路径
            content: 内容
            mode: 模式 (write/append)
            encoding: 编码
        """
        start_time = time.time()
        
        try:
            full_path = self._resolve_path(path)
            
            # 检查权限
            is_allowed, error = self._is_allowed(full_path)
            if not is_allowed:
                return FileOperationResult(
                    success=False,
                    path=path,
                    operation="write",
                    error=error,
                )
            
            # 创建目录
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            write_mode = "a" if mode == "append" else "w"
            with open(full_path, write_mode, encoding=encoding) as f:
                f.write(content)
            
            return FileOperationResult(
                success=True,
                path=path,
                operation="write",
                data={
                    "bytes_written": len(content.encode(encoding)),
                    "mode": mode,
                },
                duration_ms=(time.time() - start_time) * 1000,
            )
        
        except Exception as e:
            return FileOperationResult(
                success=False,
                path=path,
                operation="write",
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )
    
    async def list_directory(
        self,
        path: str = ".",
        pattern: str = "*",
        recursive: bool = False,
    ) -> FileOperationResult:
        """
        列出目录内容
        
        Args:
            path: 目录路径
            pattern: 文件模式
            recursive: 是否递归
        """
        start_time = time.time()
        
        try:
            full_path = self._resolve_path(path)
            
            if not full_path.exists():
                return FileOperationResult(
                    success=False,
                    path=path,
                    operation="list",
                    error="目录不存在",
                )
            
            if not full_path.is_dir():
                return FileOperationResult(
                    success=False,
                    path=path,
                    operation="list",
                    error="不是目录",
                )
            
            files = []
            if recursive:
                for item in full_path.rglob(pattern):
                    if item.is_file():
                        stat = item.stat()
                        files.append(FileInfo(
                            path=str(item.relative_to(full_path)),
                            name=item.name,
                            size=stat.st_size,
                            is_dir=False,
                            modified_time=stat.st_mtime,
                            created_time=stat.st_ctime,
                            permissions=oct(stat.st_mode)[-3:],
                        ))
            else:
                for item in full_path.glob(pattern):
                    stat = item.stat()
                    files.append(FileInfo(
                        path=str(item.name),
                        name=item.name,
                        size=stat.st_size,
                        is_dir=item.is_dir(),
                        modified_time=stat.st_mtime,
                        created_time=stat.st_ctime,
                        permissions=oct(stat.st_mode)[-3:],
                    ))
            
            return FileOperationResult(
                success=True,
                path=path,
                operation="list",
                data={
                    "files": [f.to_dict() for f in files],
                    "total": len(files),
                },
                duration_ms=(time.time() - start_time) * 1000,
            )
        
        except Exception as e:
            return FileOperationResult(
                success=False,
                path=path,
                operation="list",
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )
    
    async def search_in_file(
        self,
        path: str,
        pattern: str,
        context_lines: int = 2,
    ) -> FileOperationResult:
        """
        在文件中搜索
        
        Args:
            path: 文件路径
            pattern: 搜索模式（正则）
            context_lines: 上下文行数
        """
        start_time = time.time()
        
        try:
            full_path = self._resolve_path(path)
            
            is_allowed, error = self._is_allowed(full_path)
            if not is_allowed:
                return FileOperationResult(
                    success=False,
                    path=path,
                    operation="search",
                    error=error,
                )
            
            if not full_path.exists():
                return FileOperationResult(
                    success=False,
                    path=path,
                    operation="search",
                    error="文件不存在",
                )
            
            matches = []
            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            regex = re.compile(pattern, re.IGNORECASE)
            for i, line in enumerate(lines):
                if regex.search(line):
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    matches.append({
                        "line_number": i + 1,
                        "line": line.rstrip(),
                        "context": [l.rstrip() for l in lines[start:end]],
                    })
            
            return FileOperationResult(
                success=True,
                path=path,
                operation="search",
                data={
                    "pattern": pattern,
                    "matches": matches,
                    "total_matches": len(matches),
                },
                duration_ms=(time.time() - start_time) * 1000,
            )
        
        except Exception as e:
            return FileOperationResult(
                success=False,
                path=path,
                operation="search",
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )


class LogParser:
    """
    日志解析器
    
    解析各种格式的日志文件。
    """
    
    # 常见日志格式
    LOG_PATTERNS = {
        "nginx": r'(?P<ip>[\d.]+) - - \[(?P<time>[^\]]+)\] "(?P<method>\w+) (?P<path>[^\s]+) [^"]+" (?P<status>\d+) (?P<size>\d+)',
        "apache": r'(?P<ip>[\d.]+) - - \[(?P<time>[^\]]+)\] "(?P<method>\w+) (?P<path>[^\s]+) [^"]+" (?P<status>\d+) (?P<size>\d+)',
        "json": None,  # JSON 格式
        "syslog": r'(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>[\d:]+)\s+(?P<host>\w+)\s+(?P<process>[^\[]+)\[(?P<pid>\d+)\]:\s*(?P<message>.+)',
    }
    
    async def parse(
        self,
        content: str,
        log_format: str = "auto",
    ) -> Dict[str, Any]:
        """
        解析日志
        
        Args:
            content: 日志内容
            log_format: 日志格式
        """
        lines = content.strip().split("\n")
        parsed_lines = []
        
        if log_format == "auto":
            log_format = self._detect_format(lines[0] if lines else "")
        
        if log_format == "json":
            for line in lines:
                try:
                    parsed_lines.append(json.loads(line))
                except json.JSONDecodeError:
                    parsed_lines.append({"raw": line})
        else:
            pattern = self.LOG_PATTERNS.get(log_format)
            if pattern:
                regex = re.compile(pattern)
                for line in lines:
                    match = regex.match(line)
                    if match:
                        parsed_lines.append(match.groupdict())
                    else:
                        parsed_lines.append({"raw": line})
            else:
                parsed_lines = [{"raw": line} for line in lines]
        
        return {
            "format": log_format,
            "total_lines": len(parsed_lines),
            "lines": parsed_lines,
        }
    
    def _detect_format(self, line: str) -> str:
        """检测日志格式"""
        # 检测 JSON
        if line.strip().startswith("{"):
            try:
                json.loads(line)
                return "json"
            except json.JSONDecodeError:
                pass
        
        # 检测其他格式
        for name, pattern in self.LOG_PATTERNS.items():
            if pattern and re.match(pattern, line):
                return name
        
        return "raw"
    
    async def analyze(
        self,
        content: str,
        log_format: str = "auto",
    ) -> Dict[str, Any]:
        """
        分析日志
        
        统计错误、警告等。
        """
        parsed = await self.parse(content, log_format)
        lines = parsed["lines"]
        
        # 统计
        error_count = 0
        warning_count = 0
        info_count = 0
        
        error_patterns = [
            r"\berror\b",
            r"\bexception\b",
            r"\bfatal\b",
            r"\bfailed\b",
            r"5\d{2}",  # 5xx 状态码
        ]
        
        warning_patterns = [
            r"\bwarning\b",
            r"\bwarn\b",
            r"4\d{2}",  # 4xx 状态码
        ]
        
        for line in lines:
            line_str = str(line).lower()
            
            if any(re.search(p, line_str, re.IGNORECASE) for p in error_patterns):
                error_count += 1
            elif any(re.search(p, line_str, re.IGNORECASE) for p in warning_patterns):
                warning_count += 1
            else:
                info_count += 1
        
        return {
            "format": parsed["format"],
            "total_lines": parsed["total_lines"],
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
            "health_score": max(0, 100 - (error_count * 10 + warning_count * 2)),
        }


class FileServer(BaseToolServer):
    """
    文件操作 MCP Server
    
    提供文件读写、日志解析等工具。
    """
    
    def __init__(self, base_path: str = "."):
        super().__init__(
            name="file-tools",
            description="文件工具集：读写、搜索、日志解析"
        )
        
        self.file_ops = FileOperations(base_path)
        self.log_parser = LogParser()
        
        self._register_tools()
    
    def _register_tools(self):
        """注册所有文件工具"""
        
        @self.register_tool(ToolSchema(
            name="file_read",
            description="读取文件内容",
            input_schema={
                "type": "object",
                "required": ["path"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "起始行号",
                        "default": 0
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "结束行号"
                    }
                }
            }
        ))
        async def file_read(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            path = params.get("path")
            start_line = params.get("start_line", 0)
            end_line = params.get("end_line")
            
            result = await self.file_ops.read_file(path, start_line=start_line, end_line=end_line)
            
            if result.success:
                return ToolResult.success(result.to_dict())
            else:
                return ToolResult.error(result.error, error_code="FILE_ERROR")
        
        @self.register_tool(ToolSchema(
            name="file_write",
            description="写入文件",
            input_schema={
                "type": "object",
                "required": ["path", "content"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容"
                    },
                    "mode": {
                        "type": "string",
                        "description": "写入模式",
                        "enum": ["write", "append"],
                        "default": "write"
                    }
                }
            }
        ))
        async def file_write(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            path = params.get("path")
            content = params.get("content", "")
            mode = params.get("mode", "write")
            
            result = await self.file_ops.write_file(path, content, mode)
            
            if result.success:
                return ToolResult.success(result.to_dict())
            else:
                return ToolResult.error(result.error, error_code="FILE_ERROR")
        
        @self.register_tool(ToolSchema(
            name="file_list",
            description="列出目录内容",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径",
                        "default": "."
                    },
                    "pattern": {
                        "type": "string",
                        "description": "文件模式",
                        "default": "*"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归",
                        "default": False
                    }
                }
            }
        ))
        async def file_list(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            path = params.get("path", ".")
            pattern = params.get("pattern", "*")
            recursive = params.get("recursive", False)
            
            result = await self.file_ops.list_directory(path, pattern, recursive)
            
            if result.success:
                return ToolResult.success(result.to_dict())
            else:
                return ToolResult.error(result.error, error_code="FILE_ERROR")
        
        @self.register_tool(ToolSchema(
            name="file_search",
            description="在文件中搜索",
            input_schema={
                "type": "object",
                "required": ["path", "pattern"],
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "搜索模式（正则）"
                    },
                    "context_lines": {
                        "type": "integer",
                        "description": "上下文行数",
                        "default": 2
                    }
                }
            }
        ))
        async def file_search(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            path = params.get("path")
            pattern = params.get("pattern")
            context_lines = params.get("context_lines", 2)
            
            result = await self.file_ops.search_in_file(path, pattern, context_lines)
            
            if result.success:
                return ToolResult.success(result.to_dict())
            else:
                return ToolResult.error(result.error, error_code="FILE_ERROR")
        
        @self.register_tool(ToolSchema(
            name="log_parse",
            description="解析日志文件",
            input_schema={
                "type": "object",
                "required": ["content"],
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "日志内容"
                    },
                    "format": {
                        "type": "string",
                        "description": "日志格式 (auto/json/nginx/apache/syslog)",
                        "default": "auto"
                    }
                }
            }
        ))
        async def log_parse(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            content = params.get("content", "")
            log_format = params.get("format", "auto")
            
            result = await self.log_parser.parse(content, log_format)
            
            return ToolResult.success(result)
        
        @self.register_tool(ToolSchema(
            name="log_analyze",
            description="分析日志（统计错误、警告）",
            input_schema={
                "type": "object",
                "required": ["content"],
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "日志内容"
                    },
                    "format": {
                        "type": "string",
                        "description": "日志格式",
                        "default": "auto"
                    }
                }
            }
        ))
        async def log_analyze(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            content = params.get("content", "")
            log_format = params.get("format", "auto")
            
            result = await self.log_parser.analyze(content, log_format)
            
            return ToolResult.success(result)
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


# 便捷函数
def create_file_server(base_path: str = ".") -> FileServer:
    """创建文件 Server"""
    return FileServer(base_path)
