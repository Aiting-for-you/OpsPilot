"""
运维工具模块

提供 kubectl、Ansible、系统监控等 MCP 工具封装。

特性：
- kubectl 命令封装
- Ansible playbook 执行
- 系统监控
- 日志收集
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from opspilot.tools.base import (
    BaseToolServer,
    ToolSchema,
    ToolResult,
    ToolContext,
)


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
        }


class CommandExecutor:
    """
    命令执行器
    
    安全执行系统命令。
    """
    
    # 允许的命令白名单
    ALLOWED_COMMANDS = [
        "kubectl", "k8s", "k",
        "docker", "podman",
        "ansible", "ansible-playbook",
        "systemctl", "journalctl",
        "curl", "wget",
        "ping", "traceroute", "nslookup", "dig",
        "top", "htop", "ps", "free", "df", "du",
        "cat", "head", "tail", "grep", "awk", "sed",
        "ls", "find", "tree",
        "git",
    ]
    
    # 禁止的命令模式
    BLOCKED_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"mkfs",
        r"dd\s+if=",
        r">\s*/dev/sd",
        r"chmod\s+777",
        r":\(\)\s*\{\s*:\|:&\s*\}\s*;:",  # Fork bomb
    ]
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
    
    def validate_command(self, command: str) -> tuple[bool, str]:
        """
        验证命令安全性
        
        Returns:
            (is_valid, error_message)
        """
        # 检查禁止模式
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"禁止的命令模式: {pattern}"
        
        # 检查命令白名单
        cmd_parts = command.strip().split()
        if cmd_parts:
            base_cmd = cmd_parts[0].split("/")[-1]  # 处理路径
            if base_cmd not in self.ALLOWED_COMMANDS:
                return False, f"命令不在白名单中: {base_cmd}"
        
        return True, ""
    
    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        """
        执行命令
        
        Args:
            command: 命令字符串
            cwd: 工作目录
            env: 环境变量
        
        Returns:
            CommandResult: 执行结果
        """
        # 验证命令
        is_valid, error = self.validate_command(command)
        if not is_valid:
            return CommandResult(success=False, stderr=error)
        
        start_time = time.time()
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                
                return CommandResult(
                    success=process.returncode == 0,
                    exit_code=process.returncode or 0,
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    duration_ms=(time.time() - start_time) * 1000,
                )
            
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return CommandResult(
                    success=False,
                    stderr=f"命令执行超时 ({self.timeout}秒)",
                    duration_ms=self.timeout * 1000,
                )
        
        except Exception as e:
            return CommandResult(
                success=False,
                stderr=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )


class KubernetesTools:
    """Kubernetes 工具集"""
    
    def __init__(self, executor: CommandExecutor, kubeconfig: str = ""):
        self.executor = executor
        self.kubeconfig = kubeconfig
    
    def _build_kubectl(self, args: str, namespace: str = "default") -> str:
        """构建 kubectl 命令"""
        cmd = "kubectl"
        if self.kubeconfig:
            cmd += f" --kubeconfig={self.kubeconfig}"
        cmd += f" -n {namespace} {args}"
        return cmd
    
    async def get_pods(
        self,
        namespace: str = "default",
        label_selector: str = "",
    ) -> Dict[str, Any]:
        """获取 Pod 列表"""
        args = "get pods -o json"
        if label_selector:
            args += f" -l {label_selector}"
        
        result = await self.executor.execute(
            self._build_kubectl(args, namespace)
        )
        
        if result.success:
            try:
                data = json.loads(result.stdout)
                pods = [
                    {
                        "name": item["metadata"]["name"],
                        "namespace": item["metadata"]["namespace"],
                        "status": item["status"]["phase"],
                        "pod_ip": item["status"].get("podIP", ""),
                        "age": item["metadata"].get("creationTimestamp", ""),
                    }
                    for item in data.get("items", [])
                ]
                return {"success": True, "pods": pods}
            except json.JSONDecodeError:
                return {"success": False, "error": "JSON 解析失败"}
        
        return {"success": False, "error": result.stderr}
    
    async def get_services(self, namespace: str = "default") -> Dict[str, Any]:
        """获取 Service 列表"""
        result = await self.executor.execute(
            self._build_kubectl("get services -o json", namespace)
        )
        
        if result.success:
            try:
                data = json.loads(result.stdout)
                services = [
                    {
                        "name": item["metadata"]["name"],
                        "namespace": item["metadata"]["namespace"],
                        "type": item["spec"]["type"],
                        "cluster_ip": item["spec"].get("clusterIP", ""),
                        "ports": [
                            {"port": p["port"], "target_port": p.get("targetPort")}
                            for p in item["spec"]["ports"]
                        ],
                    }
                    for item in data.get("items", [])
                ]
                return {"success": True, "services": services}
            except json.JSONDecodeError:
                return {"success": False, "error": "JSON 解析失败"}
        
        return {"success": False, "error": result.stderr}
    
    async def describe_pod(self, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """获取 Pod 详情"""
        result = await self.executor.execute(
            self._build_kubectl(f"describe pod {pod_name}", namespace)
        )
        
        return {
            "success": result.success,
            "output": result.stdout if result.success else result.stderr,
        }
    
    async def logs(
        self,
        pod_name: str,
        namespace: str = "default",
        container: str = "",
        tail: int = 100,
    ) -> Dict[str, Any]:
        """获取 Pod 日志"""
        args = f"logs {pod_name} --tail={tail}"
        if container:
            args += f" -c {container}"
        
        result = await self.executor.execute(
            self._build_kubectl(args, namespace)
        )
        
        return {
            "success": result.success,
            "logs": result.stdout if result.success else result.stderr,
        }


class SystemTools:
    """系统工具集"""
    
    def __init__(self, executor: CommandExecutor):
        self.executor = executor
    
    async def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        # Mock 数据
        return {
            "success": True,
            "hostname": "opspilot-server-01",
            "os": "Linux",
            "kernel": "5.15.0-91-generic",
            "cpu_cores": 8,
            "memory_total_gb": 32,
            "disk_total_gb": 500,
            "uptime": "15 days, 3:45:22",
        }
    
    async def get_cpu_usage(self) -> Dict[str, Any]:
        """获取 CPU 使用率"""
        result = await self.executor.execute("top -bn1 | head -5")
        
        # Mock 数据
        return {
            "success": True,
            "usage_percent": 45.2,
            "user_percent": 25.3,
            "system_percent": 12.8,
            "idle_percent": 54.8,
            "load_avg": [1.25, 1.15, 1.05],
        }
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        result = await self.executor.execute("free -m")
        
        # Mock 数据
        return {
            "success": True,
            "total_mb": 32768,
            "used_mb": 16384,
            "free_mb": 8192,
            "cache_mb": 8192,
            "usage_percent": 50.0,
        }
    
    async def get_disk_usage(self) -> Dict[str, Any]:
        """获取磁盘使用情况"""
        result = await self.executor.execute("df -h")
        
        # Mock 数据
        return {
            "success": True,
            "disks": [
                {
                    "mount": "/",
                    "total_gb": 500,
                    "used_gb": 250,
                    "available_gb": 250,
                    "usage_percent": 50.0,
                },
                {
                    "mount": "/data",
                    "total_gb": 1000,
                    "used_gb": 350,
                    "available_gb": 650,
                    "usage_percent": 35.0,
                },
            ],
        }
    
    async def list_processes(self, top_n: int = 10) -> Dict[str, Any]:
        """列出进程"""
        # Mock 数据
        return {
            "success": True,
            "processes": [
                {"pid": 1, "name": "systemd", "cpu": 0.0, "memory": 0.5},
                {"pid": 1234, "name": "python", "cpu": 15.2, "memory": 8.5},
                {"pid": 2345, "name": "node", "cpu": 12.8, "memory": 6.2},
                {"pid": 3456, "name": "nginx", "cpu": 2.1, "memory": 1.5},
                {"pid": 4567, "name": "redis-server", "cpu": 1.5, "memory": 3.2},
            ],
        }


class DevOpsServer(BaseToolServer):
    """
    运维 MCP Server
    
    提供 Kubernetes、系统监控等工具。
    """
    
    def __init__(
        self,
        kubeconfig: str = "",
        command_timeout: int = 60,
    ):
        super().__init__(
            name="devops-tools",
            description="运维工具集：Kubernetes、系统监控、日志查询"
        )
        
        self.executor = CommandExecutor(timeout=command_timeout)
        self.k8s = KubernetesTools(self.executor, kubeconfig)
        self.system = SystemTools(self.executor)
        
        self._register_tools()
    
    def _register_tools(self):
        """注册所有运维工具"""
        
        # ==================== Kubernetes 工具 ====================
        
        @self.register_tool(ToolSchema(
            name="k8s_get_pods",
            description="获取 Kubernetes Pod 列表",
            input_schema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "命名空间",
                        "default": "default"
                    },
                    "label_selector": {
                        "type": "string",
                        "description": "标签选择器"
                    }
                }
            }
        ))
        async def k8s_get_pods(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            namespace = params.get("namespace", "default")
            label_selector = params.get("label_selector", "")
            
            result = await self.k8s.get_pods(namespace, label_selector)
            
            if result["success"]:
                return ToolResult.success(result)
            else:
                return ToolResult.error(result.get("error", "未知错误"))
        
        @self.register_tool(ToolSchema(
            name="k8s_get_services",
            description="获取 Kubernetes Service 列表",
            input_schema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "命名空间",
                        "default": "default"
                    }
                }
            }
        ))
        async def k8s_get_services(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            namespace = params.get("namespace", "default")
            result = await self.k8s.get_services(namespace)
            
            if result["success"]:
                return ToolResult.success(result)
            else:
                return ToolResult.error(result.get("error", "未知错误"))
        
        @self.register_tool(ToolSchema(
            name="k8s_describe_pod",
            description="获取 Pod 详情",
            input_schema={
                "type": "object",
                "required": ["pod_name"],
                "properties": {
                    "pod_name": {
                        "type": "string",
                        "description": "Pod 名称"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "命名空间",
                        "default": "default"
                    }
                }
            }
        ))
        async def k8s_describe_pod(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            pod_name = params.get("pod_name")
            namespace = params.get("namespace", "default")
            
            result = await self.k8s.describe_pod(pod_name, namespace)
            
            if result["success"]:
                return ToolResult.success({"output": result["output"]})
            else:
                return ToolResult.error(result.get("output", "获取失败"))
        
        @self.register_tool(ToolSchema(
            name="k8s_logs",
            description="获取 Pod 日志",
            input_schema={
                "type": "object",
                "required": ["pod_name"],
                "properties": {
                    "pod_name": {
                        "type": "string",
                        "description": "Pod 名称"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "命名空间",
                        "default": "default"
                    },
                    "container": {
                        "type": "string",
                        "description": "容器名称"
                    },
                    "tail": {
                        "type": "integer",
                        "description": "日志行数",
                        "default": 100
                    }
                }
            }
        ))
        async def k8s_logs(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            pod_name = params.get("pod_name")
            namespace = params.get("namespace", "default")
            container = params.get("container", "")
            tail = params.get("tail", 100)
            
            result = await self.k8s.logs(pod_name, namespace, container, tail)
            
            if result["success"]:
                return ToolResult.success({"logs": result["logs"]})
            else:
                return ToolResult.error(result.get("logs", "获取失败"))
        
        # ==================== 系统监控工具 ====================
        
        @self.register_tool(ToolSchema(
            name="system_info",
            description="获取系统信息",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def system_info(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            result = await self.system.get_system_info()
            return ToolResult.success(result)
        
        @self.register_tool(ToolSchema(
            name="system_cpu",
            description="获取 CPU 使用率",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def system_cpu(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            result = await self.system.get_cpu_usage()
            return ToolResult.success(result)
        
        @self.register_tool(ToolSchema(
            name="system_memory",
            description="获取内存使用情况",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def system_memory(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            result = await self.system.get_memory_usage()
            return ToolResult.success(result)
        
        @self.register_tool(ToolSchema(
            name="system_disk",
            description="获取磁盘使用情况",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ))
        async def system_disk(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            result = await self.system.get_disk_usage()
            return ToolResult.success(result)
        
        @self.register_tool(ToolSchema(
            name="system_processes",
            description="列出进程",
            input_schema={
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "返回数量",
                        "default": 10
                    }
                }
            }
        ))
        async def system_processes(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            top_n = params.get("top_n", 10)
            result = await self.system.list_processes(top_n)
            return ToolResult.success(result)
        
        # ==================== 命令执行工具 ====================
        
        @self.register_tool(ToolSchema(
            name="execute_command",
            description="安全执行系统命令",
            input_schema={
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的命令（需在白名单中）"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "超时时间（秒）",
                        "default": 60
                    }
                }
            }
        ))
        async def execute_command(params: Dict[str, Any], context: ToolContext) -> ToolResult:
            command = params.get("command", "")
            
            result = await self.executor.execute(command)
            
            if result.success:
                return ToolResult.success(result.to_dict())
            else:
                return ToolResult.error(
                    result.stderr or "命令执行失败",
                    error_code="COMMAND_ERROR",
                )
    
    async def health_check(self) -> bool:
        """健康检查"""
        return True


# 便捷函数
def create_devops_server(
    kubeconfig: str = "",
    command_timeout: int = 60,
) -> DevOpsServer:
    """创建运维 Server"""
    return DevOpsServer(kubeconfig, command_timeout)
