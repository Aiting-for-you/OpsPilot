"""
API 模块单元测试
"""
import pytest
from fastapi.testclient import TestClient

from opspilot.main import create_app


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


class TestRootEndpoint:
    """根端点测试"""

    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "opspilot"
        assert "version" in data


class TestHealthEndpoint:
    """健康检查端点测试"""

    def test_health(self, client):
        """测试健康检查"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestTaskEndpoints:
    """任务端点测试"""

    def test_create_task(self, client):
        """测试创建任务"""
        response = client.post(
            "/api/v1/tasks",
            json={"user_input": "查询华南供应商"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data

    def test_create_task_empty_input(self, client):
        """测试空输入"""
        response = client.post(
            "/api/v1/tasks",
            json={"user_input": ""}
        )

        assert response.status_code == 422  # Validation error

    def test_get_task_status_not_found(self, client):
        """测试查询不存在的任务"""
        response = client.get("/api/v1/tasks/nonexistent")

        assert response.status_code == 404

    def test_get_task_result_not_found(self, client):
        """测试获取不存在任务的结果"""
        response = client.get("/api/v1/tasks/nonexistent/result")

        assert response.status_code == 404


class TestToolEndpoints:
    """工具端点测试"""

    def test_list_tools(self, client):
        """测试获取工具列表"""
        response = client.get("/api/v1/tools")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["tools"]) > 0

    def test_call_tool(self, client):
        """测试调用工具"""
        response = client.post(
            "/api/v1/tools/call",
            json={
                "tool_name": "query_supplier",
                "params": {"region": "华南"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_call_nonexistent_tool(self, client):
        """测试调用不存在的工具"""
        response = client.post(
            "/api/v1/tools/call",
            json={
                "tool_name": "nonexistent_tool",
                "params": {}
            }
        )

        assert response.status_code == 404


class TestMemoryEndpoints:
    """记忆端点测试"""

    def test_store_memory(self, client):
        """测试存储记忆"""
        response = client.post(
            "/api/v1/memory/store",
            json={
                "content": "测试记忆内容",
                "memory_type": "short_term"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_search_memory(self, client):
        """测试搜索记忆"""
        # 先存储一些记忆
        client.post(
            "/api/v1/memory/store",
            json={"content": "苹果是一种水果"}
        )

        # 搜索
        response = client.post(
            "/api/v1/memory/search",
            json={"query": "水果"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestSOPEndpoints:
    """SOP 端点测试"""

    def test_list_sops(self, client):
        """测试获取 SOP 列表"""
        response = client.get("/api/v1/sop/list")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "create_order" in data["sops"]

    def test_execute_sop(self, client):
        """测试执行 SOP"""
        response = client.post(
            "/api/v1/sop/execute",
            json={
                "sop_name": "query_supplier",
                "variables": {"region": "华南"}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "sop_name" in data

    def test_execute_nonexistent_sop(self, client):
        """测试执行不存在的 SOP"""
        response = client.post(
            "/api/v1/sop/execute",
            json={
                "sop_name": "nonexistent_sop",
                "variables": {}
            }
        )

        assert response.status_code == 404


class TestKnowledgeEndpoints:
    """知识库端点测试"""

    def test_query_knowledge(self, client):
        """测试查询知识库"""
        response = client.post(
            "/api/v1/knowledge/query",
            json={"query": "采购审批"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestIntegration:
    """集成测试"""

    def test_full_task_flow(self, client):
        """测试完整任务流程"""
        # 1. 创建任务
        create_response = client.post(
            "/api/v1/tasks",
            json={"user_input": "查询华南供应商"}
        )
        assert create_response.status_code == 200
        task_id = create_response.json()["task_id"]

        # 2. 查询状态
        status_response = client.get(f"/api/v1/tasks/{task_id}")
        assert status_response.status_code == 200

        # 3. 获取结果
        result_response = client.get(f"/api/v1/tasks/{task_id}/result")
        assert result_response.status_code == 200

