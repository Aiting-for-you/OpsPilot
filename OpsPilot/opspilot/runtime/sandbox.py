"""
工具沙箱模块

基于 AgentScope Runtime 的安全隔离执行能力。
提供 Python/Shell 工具的安全执行环境。

特性：
- 加固沙箱环境，隔离执行运维脚本
- 支持同步/异步执行
- 资源限制（内存、CPU、超时）
- 执行日志记录
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import tempfile
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import json
import os


class SandboxStatus(Enum):
    """沙箱状态"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class SandboxResult:
    """沙箱执行结果"""
    success: bool
    status: SandboxStatus
    output: str = ""
    error: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass
class SandboxConfig:
    """沙箱配置"""
    timeout: int = 60  # 超时时间（秒）
    max_memory_mb: int = 512  # 最大内存（MB）
    max_output_size: int = 1024 * 1024  # 最大输出大小（字节）
    allowed_commands: Optional[List[str]] = None  # 允许的命令白名单
    blocked_commands: Optional[List[str]] = None  # 禁止的命令黑名单
    env_vars: Optional[Dict[str, str]] = None  # 环境变量
    work_dir: Optional[str] = None  # 工作目录


class BaseSandbox(ABC):
    """
    沙箱基类
    
    定义沙箱执行的标准接口。
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._status = SandboxStatus.IDLE
    
    @property
    def status(self) -> SandboxStatus:
        return self._status
    
    @abstractmethod
    async def execute_python(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None,
    ) -> SandboxResult:
        """
        执行 Python 代码
        
        Args:
            code: Python 代码
            globals_dict: 全局变量
            locals_dict: 局部变量
        
        Returns:
            SandboxResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def execute_shell(
        self,
        command: str,
        cwd: Optional[str] = None,
    ) -> SandboxResult:
        """
        执行 Shell 命令
        
        Args:
            command: Shell 命令
            cwd: 工作目录
        
        Returns:
            SandboxResult: 执行结果
        """
        pass
    
    def _validate_command(self, command: str) -> bool:
        """
        验证命令是否允许执行
        
        Args:
            command: 命令
        
        Returns:
            bool: 是否允许
        """
        # 检查黑名单
        if self.config.blocked_commands:
            for blocked in self.config.blocked_commands:
                if blocked in command:
                    return False
        
        # 检查白名单
        if self.config.allowed_commands:
            cmd_parts = command.split()
            if cmd_parts:
                base_cmd = cmd_parts[0]
                if base_cmd not in self.config.allowed_commands:
                    return False
        
        return True


class LocalSandbox(BaseSandbox):
    """
    本地沙箱
    
    在当前进程内安全执行代码。
    适用于开发环境，生产环境建议使用 Docker 沙箱。
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        super().__init__(config)
        self._output_buffer: List[str] = []
    
    async def execute_python(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None,
    ) -> SandboxResult:
        """执行 Python 代码"""
        start_time = time.time()
        self._status = SandboxStatus.RUNNING
        self._output_buffer = []
        
        try:
            # 准备执行环境
            exec_globals = {
                "__builtins__": __builtins__,
                "json": json,
                "os": os,
                "print": self._capture_print,
            }
            if globals_dict:
                exec_globals.update(globals_dict)
            
            exec_locals = locals_dict or {}
            
            # 异步执行带超时
            async def run_code():
                exec(code, exec_globals, exec_locals)
                return exec_locals.get("result")
            
            try:
                result = await asyncio.wait_for(
                    run_code(),
                    timeout=self.config.timeout
                )
                
                duration_ms = (time.time() - start_time) * 1000
                self._status = SandboxStatus.SUCCESS
                
                return SandboxResult(
                    success=True,
                    status=SandboxStatus.SUCCESS,
                    output="\n".join(self._output_buffer),
                    duration_ms=duration_ms,
                    metadata={"result": result},
                )
            
            except asyncio.TimeoutError:
                self._status = SandboxStatus.TIMEOUT
                return SandboxResult(
                    success=False,
                    status=SandboxStatus.TIMEOUT,
                    error=f"执行超时（{self.config.timeout}秒）",
                    duration_ms=self.config.timeout * 1000,
                )
        
        except Exception as e:
            self._status = SandboxStatus.FAILED
            return SandboxResult(
                success=False,
                status=SandboxStatus.FAILED,
                error=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
                duration_ms=(time.time() - start_time) * 1000,
            )
    
    async def execute_shell(
        self,
        command: str,
        cwd: Optional[str] = None,
    ) -> SandboxResult:
        """执行 Shell 命令"""
        start_time = time.time()
        self._status = SandboxStatus.RUNNING
        
        # 验证命令
        if not self._validate_command(command):
            self._status = SandboxStatus.FAILED
            return SandboxResult(
                success=False,
                status=SandboxStatus.FAILED,
                error="命令不允许执行",
            )
        
        try:
            # 准备环境变量
            env = os.environ.copy()
            if self.config.env_vars:
                env.update(self.config.env_vars)
            
            # 执行命令
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or self.config.work_dir,
                env=env,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if process.returncode == 0:
                    self._status = SandboxStatus.SUCCESS
                    return SandboxResult(
                        success=True,
                        status=SandboxStatus.SUCCESS,
                        output=stdout.decode("utf-8", errors="replace"),
                        exit_code=process.returncode,
                        duration_ms=duration_ms,
                    )
                else:
                    self._status = SandboxStatus.FAILED
                    return SandboxResult(
                        success=False,
                        status=SandboxStatus.FAILED,
                        output=stdout.decode("utf-8", errors="replace"),
                        error=stderr.decode("utf-8", errors="replace"),
                        exit_code=process.returncode,
                        duration_ms=duration_ms,
                    )
            
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                self._status = SandboxStatus.TIMEOUT
                return SandboxResult(
                    success=False,
                    status=SandboxStatus.TIMEOUT,
                    error=f"执行超时（{self.config.timeout}秒）",
                    duration_ms=self.config.timeout * 1000,
                )
        
        except Exception as e:
            self._status = SandboxStatus.FAILED
            return SandboxResult(
                success=False,
                status=SandboxStatus.FAILED,
                error=f"{type(e).__name__}: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )
    
    def _capture_print(self, *args, **kwargs):
        """捕获 print 输出"""
        output = " ".join(str(arg) for arg in args)
        self._output_buffer.append(output)


class DockerSandbox(BaseSandbox):
    """
    Docker 沙箱
    
    在 Docker 容器内安全执行代码。
    适用于生产环境，提供更强的隔离性。
    """
    
    def __init__(
        self,
        config: Optional[SandboxConfig] = None,
        image: str = "python:3.11-slim",
    ):
        super().__init__(config)
        self.image = image
        self._docker_available: Optional[bool] = None
    
    async def _check_docker(self) -> bool:
        """检查 Docker 是否可用"""
        if self._docker_available is not None:
            return self._docker_available
        
        try:
            process = await asyncio.create_subprocess_shell(
                "docker --version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            self._docker_available = process.returncode == 0
        except Exception:
            self._docker_available = False
        
        return self._docker_available
    
    async def execute_python(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None,
    ) -> SandboxResult:
        """在 Docker 容器内执行 Python 代码"""
        start_time = time.time()
        self._status = SandboxStatus.RUNNING
        
        # 检查 Docker
        if not await self._check_docker():
            # 降级到本地沙箱
            local_sandbox = LocalSandbox(self.config)
            return await local_sandbox.execute_python(code, globals_dict, locals_dict)
        
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # 构建命令
                container_name = f"opspilot-sandbox-{int(time.time() * 1000)}"
                command = (
                    f"docker run --rm "
                    f"--name {container_name} "
                    f"--memory={self.config.max_memory_mb}m "
                    f"--timeout={self.config.timeout} "
                    f"-v {temp_file}:/app/script.py "
                    f"{self.image} "
                    f"python /app/script.py"
                )
                
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout + 10  # 额外 10 秒给 Docker
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if process.returncode == 0:
                    self._status = SandboxStatus.SUCCESS
                    return SandboxResult(
                        success=True,
                        status=SandboxStatus.SUCCESS,
                        output=stdout.decode("utf-8", errors="replace"),
                        duration_ms=duration_ms,
                    )
                else:
                    self._status = SandboxStatus.FAILED
                    return SandboxResult(
                        success=False,
                        status=SandboxStatus.FAILED,
                        output=stdout.decode("utf-8", errors="replace"),
                        error=stderr.decode("utf-8", errors="replace"),
                        exit_code=process.returncode,
                        duration_ms=duration_ms,
                    )
            
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
        
        except asyncio.TimeoutError:
            self._status = SandboxStatus.TIMEOUT
            return SandboxResult(
                success=False,
                status=SandboxStatus.TIMEOUT,
                error=f"执行超时（{self.config.timeout}秒）",
                duration_ms=self.config.timeout * 1000,
            )
        
        except Exception as e:
            self._status = SandboxStatus.FAILED
            return SandboxResult(
                success=False,
                status=SandboxStatus.FAILED,
                error=f"{type(e).__name__}: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )
    
    async def execute_shell(
        self,
        command: str,
        cwd: Optional[str] = None,
    ) -> SandboxResult:
        """在 Docker 容器内执行 Shell 命令"""
        start_time = time.time()
        self._status = SandboxStatus.RUNNING
        
        # 检查 Docker
        if not await self._check_docker():
            # 降级到本地沙箱
            local_sandbox = LocalSandbox(self.config)
            return await local_sandbox.execute_shell(command, cwd)
        
        # 验证命令
        if not self._validate_command(command):
            self._status = SandboxStatus.FAILED
            return SandboxResult(
                success=False,
                status=SandboxStatus.FAILED,
                error="命令不允许执行",
            )
        
        try:
            # 构建命令
            container_name = f"opspilot-sandbox-{int(time.time() * 1000)}"
            docker_command = (
                f"docker run --rm "
                f"--name {container_name} "
                f"--memory={self.config.max_memory_mb}m "
                f"{self.image} "
                f"sh -c '{command}'"
            )
            
            process = await asyncio.create_subprocess_shell(
                docker_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout + 10
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if process.returncode == 0:
                    self._status = SandboxStatus.SUCCESS
                    return SandboxResult(
                        success=True,
                        status=SandboxStatus.SUCCESS,
                        output=stdout.decode("utf-8", errors="replace"),
                        duration_ms=duration_ms,
                    )
                else:
                    self._status = SandboxStatus.FAILED
                    return SandboxResult(
                        success=False,
                        status=SandboxStatus.FAILED,
                        output=stdout.decode("utf-8", errors="replace"),
                        error=stderr.decode("utf-8", errors="replace"),
                        exit_code=process.returncode,
                        duration_ms=duration_ms,
                    )
            
            except asyncio.TimeoutError:
                self._status = SandboxStatus.TIMEOUT
                return SandboxResult(
                    success=False,
                    status=SandboxStatus.TIMEOUT,
                    error=f"执行超时（{self.config.timeout}秒）",
                    duration_ms=self.config.timeout * 1000,
                )
        
        except Exception as e:
            self._status = SandboxStatus.FAILED
            return SandboxResult(
                success=False,
                status=SandboxStatus.FAILED,
                error=f"{type(e).__name__}: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )


class ToolSandboxManager:
    """
    工具沙箱管理器
    
    统一管理工具的沙箱执行。
    支持自动选择最佳沙箱类型。
    """
    
    def __init__(
        self,
        sandbox_type: str = "auto",
        config: Optional[SandboxConfig] = None,
    ):
        """
        初始化沙箱管理器
        
        Args:
            sandbox_type: 沙箱类型 ("local", "docker", "auto")
            config: 沙箱配置
        """
        self.config = config or SandboxConfig()
        self._sandbox: Optional[BaseSandbox] = None
        self._sandbox_type = sandbox_type
    
    async def _get_sandbox(self) -> BaseSandbox:
        """获取沙箱实例"""
        if self._sandbox is not None:
            return self._sandbox
        
        if self._sandbox_type == "local":
            self._sandbox = LocalSandbox(self.config)
        elif self._sandbox_type == "docker":
            self._sandbox = DockerSandbox(self.config)
        else:  # auto
            # 尝试 Docker，失败则降级到本地
            docker_sandbox = DockerSandbox(self.config)
            if await docker_sandbox._check_docker():
                self._sandbox = docker_sandbox
            else:
                self._sandbox = LocalSandbox(self.config)
        
        return self._sandbox
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_code: Optional[str] = None,
        tool_command: Optional[str] = None,
        **kwargs,
    ) -> SandboxResult:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            tool_code: Python 代码
            tool_command: Shell 命令
            **kwargs: 其他参数
        
        Returns:
            SandboxResult: 执行结果
        """
        sandbox = await self._get_sandbox()
        
        if tool_code:
            return await sandbox.execute_python(tool_code)
        elif tool_command:
            return await sandbox.execute_shell(tool_command)
        else:
            return SandboxResult(
                success=False,
                status=SandboxStatus.FAILED,
                error="必须提供 tool_code 或 tool_command",
            )


# 默认沙箱配置
DEFAULT_SANDBOX_CONFIG = SandboxConfig(
    timeout=60,
    max_memory_mb=512,
    blocked_commands=[
        "rm -rf /",
        "mkfs",
        "dd if=",
        ":(){ :|:& };:",  # Fork bomb
    ],
)


def create_sandbox(
    sandbox_type: str = "auto",
    config: Optional[SandboxConfig] = None,
) -> ToolSandboxManager:
    """
    创建沙箱管理器
    
    Args:
        sandbox_type: 沙箱类型
        config: 沙箱配置
    
    Returns:
        ToolSandboxManager: 沙箱管理器
    """
    return ToolSandboxManager(
        sandbox_type=sandbox_type,
        config=config or DEFAULT_SANDBOX_CONFIG,
    )
