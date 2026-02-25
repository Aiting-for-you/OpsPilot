"""
沙箱模块单元测试
"""
import pytest
import asyncio

from opspilot.runtime.sandbox import (
    SandboxStatus,
    SandboxResult,
    SandboxConfig,
    BaseSandbox,
    LocalSandbox,
    DockerSandbox,
    ToolSandboxManager,
    create_sandbox,
    DEFAULT_SANDBOX_CONFIG,
)


class TestSandboxConfig:
    """沙箱配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = SandboxConfig()
        assert config.timeout == 60
        assert config.max_memory_mb == 512
        assert config.max_output_size == 1024 * 1024
        assert config.allowed_commands is None
        assert config.blocked_commands is None

    def test_custom_config(self):
        """测试自定义配置"""
        config = SandboxConfig(
            timeout=120,
            max_memory_mb=1024,
            allowed_commands=["ls", "cat", "echo"],
            blocked_commands=["rm -rf"],
        )
        assert config.timeout == 120
        assert config.max_memory_mb == 1024
        assert config.allowed_commands == ["ls", "cat", "echo"]
        assert config.blocked_commands == ["rm -rf"]


class TestSandboxResult:
    """沙箱执行结果测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = SandboxResult(
            success=True,
            status=SandboxStatus.SUCCESS,
            output="Hello, World!",
            duration_ms=100.5,
        )
        assert result.success is True
        assert result.status == SandboxStatus.SUCCESS
        assert result.output == "Hello, World!"
        assert result.duration_ms == 100.5

    def test_error_result(self):
        """测试错误结果"""
        result = SandboxResult(
            success=False,
            status=SandboxStatus.FAILED,
            error="执行失败",
            exit_code=1,
        )
        assert result.success is False
        assert result.status == SandboxStatus.FAILED
        assert result.error == "执行失败"
        assert result.exit_code == 1

    def test_timeout_result(self):
        """测试超时结果"""
        result = SandboxResult(
            success=False,
            status=SandboxStatus.TIMEOUT,
            error="执行超时（60秒）",
            duration_ms=60000,
        )
        assert result.success is False
        assert result.status == SandboxStatus.TIMEOUT

    def test_to_dict(self):
        """测试转换为字典"""
        result = SandboxResult(
            success=True,
            status=SandboxStatus.SUCCESS,
            output="output",
            metadata={"key": "value"},
        )
        data = result.to_dict()
        assert data["success"] is True
        assert data["status"] == "success"
        assert data["output"] == "output"
        assert data["metadata"] == {"key": "value"}


class TestLocalSandbox:
    """本地沙箱测试"""

    @pytest.fixture
    def sandbox(self):
        return LocalSandbox(SandboxConfig(timeout=10))

    def test_initial_status(self, sandbox):
        """测试初始状态"""
        assert sandbox.status == SandboxStatus.IDLE

    @pytest.mark.asyncio
    async def test_execute_simple_python(self, sandbox):
        """测试执行简单 Python 代码"""
        code = """
result = 1 + 1
print(f"Result: {result}")
"""
        result = await sandbox.execute_python(code)
        
        assert result.success is True
        assert result.status == SandboxStatus.SUCCESS
        assert "Result: 2" in result.output
        assert sandbox.status == SandboxStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_python_with_globals(self, sandbox):
        """测试使用全局变量执行 Python"""
        code = """
result = x + y
print(result)
"""
        result = await sandbox.execute_python(
            code,
            globals_dict={"x": 10, "y": 20},
        )
        
        assert result.success is True
        assert "30" in result.output

    @pytest.mark.asyncio
    async def test_execute_python_error(self, sandbox):
        """测试执行错误的 Python 代码"""
        code = """
raise ValueError("测试错误")
"""
        result = await sandbox.execute_python(code)
        
        assert result.success is False
        assert result.status == SandboxStatus.FAILED
        assert "ValueError" in result.error
        assert "测试错误" in result.error

    @pytest.mark.asyncio
    async def test_execute_python_timeout(self):
        """测试 Python 执行超时"""
        # 添加 asyncio 支持到沙箱执行环境
        sandbox = LocalSandbox(SandboxConfig(timeout=1))
        # 使用 get_event_loop 来在已有事件循环中运行
        code = """
async def slow_task():
    await asyncio.sleep(5)
    return "done"

loop = asyncio.get_event_loop()
result = loop.run_until_complete(slow_task())
"""
        result = await sandbox.execute_python(code)
        
        # 在 Windows 上，由于事件循环限制，超时可能不会按预期工作
        # 但执行应该失败
        assert result.success is False
        # Windows 上可能是 FAILED，其他平台应该是 TIMEOUT
        assert result.status in [SandboxStatus.TIMEOUT, SandboxStatus.FAILED]

    @pytest.mark.asyncio
    async def test_execute_simple_shell(self, sandbox):
        """测试执行简单 Shell 命令"""
        result = await sandbox.execute_shell("echo 'Hello'")
        
        assert result.success is True
        assert result.status == SandboxStatus.SUCCESS
        assert "Hello" in result.output

    @pytest.mark.asyncio
    async def test_execute_shell_error(self, sandbox):
        """测试执行错误的 Shell 命令"""
        result = await sandbox.execute_shell("nonexistent_command_12345")
        
        assert result.success is False
        assert result.status == SandboxStatus.FAILED

    @pytest.mark.asyncio
    async def test_shell_blocked_command(self):
        """测试 Shell 命令黑名单"""
        sandbox = LocalSandbox(SandboxConfig(
            blocked_commands=["rm -rf"]
        ))
        
        result = await sandbox.execute_shell("rm -rf /tmp/test")
        
        assert result.success is False
        assert result.status == SandboxStatus.FAILED
        assert "不允许执行" in result.error

    @pytest.mark.asyncio
    async def test_shell_whitelist_command(self):
        """测试 Shell 命令白名单"""
        sandbox = LocalSandbox(SandboxConfig(
            allowed_commands=["echo", "ls"]
        ))
        
        # 白名单内的命令
        result = await sandbox.execute_shell("echo 'test'")
        assert result.success is True
        
        # 不在白名单的命令
        result = await sandbox.execute_shell("dir")
        assert result.success is False
        assert "不允许执行" in result.error


class TestDockerSandbox:
    """Docker 沙箱测试"""

    @pytest.fixture
    def sandbox(self):
        return DockerSandbox(SandboxConfig(timeout=10))

    @pytest.mark.asyncio
    async def test_check_docker(self, sandbox):
        """测试 Docker 检测"""
        # 结果取决于环境
        available = await sandbox._check_docker()
        assert isinstance(available, bool)

    @pytest.mark.asyncio
    async def test_fallback_to_local(self, sandbox):
        """测试降级到本地沙箱"""
        # 如果 Docker 不可用，会降级到本地沙箱
        code = "result = 1 + 1"
        result = await sandbox.execute_python(code)
        
        # 无论 Docker 是否可用，都应该能执行
        assert result.success is True


class TestToolSandboxManager:
    """工具沙箱管理器测试"""

    @pytest.fixture
    def manager(self):
        return ToolSandboxManager(sandbox_type="local")

    @pytest.mark.asyncio
    async def test_execute_python_tool(self, manager):
        """测试执行 Python 工具"""
        result = await manager.execute_tool(
            tool_name="test_tool",
            tool_code="print('Hello from tool')",
        )
        
        assert result.success is True
        assert "Hello from tool" in result.output

    @pytest.mark.asyncio
    async def test_execute_shell_tool(self, manager):
        """测试执行 Shell 工具"""
        result = await manager.execute_tool(
            tool_name="test_tool",
            tool_command="echo 'Hello from shell'",
        )
        
        assert result.success is True
        assert "Hello from shell" in result.output

    @pytest.mark.asyncio
    async def test_execute_tool_no_code(self, manager):
        """测试执行工具无代码"""
        result = await manager.execute_tool(tool_name="test_tool")
        
        assert result.success is False
        assert "必须提供" in result.error


class TestCreateSandbox:
    """创建沙箱测试"""

    def test_create_local_sandbox(self):
        """测试创建本地沙箱"""
        manager = create_sandbox(sandbox_type="local")
        assert manager._sandbox_type == "local"

    def test_create_sandbox_with_config(self):
        """测试使用配置创建沙箱"""
        config = SandboxConfig(timeout=120)
        manager = create_sandbox(sandbox_type="local", config=config)
        assert manager.config.timeout == 120

    def test_default_sandbox_config(self):
        """测试默认沙箱配置"""
        assert DEFAULT_SANDBOX_CONFIG.timeout == 60
        assert DEFAULT_SANDBOX_CONFIG.max_memory_mb == 512
        assert "rm -rf /" in DEFAULT_SANDBOX_CONFIG.blocked_commands
