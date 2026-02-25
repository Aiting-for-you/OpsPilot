"""
框架集成测试

验证 LangChain 和 AgentScope 集成是否正确。
"""

import pytest


class TestLangChainIntegration:
    """测试 LangChain 集成"""
    
    def test_memory_chromadb_available(self):
        """测试 ChromaDB 向量存储是否可用"""
        try:
            from opspilot.memory import LANGCHAIN_AVAILABLE, ChromaDBStore
            
            if LANGCHAIN_AVAILABLE:
                assert ChromaDBStore is not None
                print("✅ ChromaDB 向量存储可用")
            else:
                print("⚠️ LangChain 未安装，ChromaDB 不可用")
        except ImportError as e:
            pytest.skip(f"ChromaDB 导入失败: {e}")
    
    def test_redis_store_available(self):
        """测试 Redis 会话存储是否可用"""
        try:
            from opspilot.memory import REDIS_AVAILABLE, RedisSessionStore
            
            if REDIS_AVAILABLE:
                assert RedisSessionStore is not None
                print("✅ Redis 会话存储可用")
            else:
                print("⚠️ Redis 未安装")
        except ImportError as e:
            pytest.skip(f"Redis 导入失败: {e}")
    
    def test_long_term_memory_uses_chroma(self):
        """测试长期记忆默认使用 ChromaDB"""
        from opspilot.memory import LongTermMemory, LANGCHAIN_AVAILABLE
        
        if LANGCHAIN_AVAILABLE:
            memory = LongTermMemory()
            assert memory.is_using_chroma
            print("✅ 长期记忆默认使用 ChromaDB")
        else:
            # 降级模式
            memory = LongTermMemory()
            assert not memory.is_using_chroma
            print("⚠️ LangChain 不可用，降级到内存存储")
    
    def test_langchain_tools_available(self):
        """测试 LangChain 工具适配器是否可用"""
        try:
            from opspilot.tools import (
                LANGCHAIN_AVAILABLE,
                MCPToolWrapper,
                OpsToolRegistry,
            )
            
            if LANGCHAIN_AVAILABLE:
                assert MCPToolWrapper is not None
                assert OpsToolRegistry is not None
                print("✅ LangChain 工具适配器可用")
            else:
                print("⚠️ LangChain 未安装")
        except ImportError as e:
            pytest.skip(f"工具适配器导入失败: {e}")
    
    def test_embeddings_available(self):
        """测试 LangChain Embeddings 是否可用"""
        try:
            from opspilot.tools import (
                LANGCHAIN_EMBEDDINGS_AVAILABLE,
                ToolEmbeddingsManager,
            )
            
            if LANGCHAIN_EMBEDDINGS_AVAILABLE:
                assert ToolEmbeddingsManager is not None
                print("✅ LangChain Embeddings 可用")
            else:
                print("⚠️ LangChain Embeddings 未安装")
        except ImportError as e:
            pytest.skip(f"Embeddings 导入失败: {e}")
    
    def test_chains_available(self):
        """测试 LangChain LCEL 链是否可用"""
        try:
            from opspilot.chains import (
                OpsChainExecutor,
                RAGChain,
                ToolChain,
            )
            
            print("✅ LangChain LCEL 链可用")
        except ImportError as e:
            pytest.skip(f"Chains 导入失败: {e}")


class TestAgentScopeIntegration:
    """测试 AgentScope 集成"""
    
    def test_agentscope_available(self):
        """测试 AgentScope 是否可用"""
        try:
            from opspilot.agents import AGENTSCOPE_AVAILABLE, AgentScopeAdapter
            
            if AGENTSCOPE_AVAILABLE:
                assert AgentScopeAdapter is not None
                print("✅ AgentScope 可用")
            else:
                print("⚠️ AgentScope 未安装，使用独立模式")
        except ImportError as e:
            pytest.skip(f"AgentScope 导入失败: {e}")
    
    def test_ops_agent_base_available(self):
        """测试 OpsAgentBase 是否可用"""
        try:
            from opspilot.agents import OpsAgentBase, AGENTSCOPE_AVAILABLE
            
            assert OpsAgentBase is not None
            
            if AGENTSCOPE_AVAILABLE:
                print("✅ OpsAgentBase 可用（AgentScope 模式）")
            else:
                print("✅ OpsAgentBase 可用（独立模式）")
        except ImportError as e:
            pytest.skip(f"OpsAgentBase 导入失败: {e}")
    
    def test_message_hub_available(self):
        """测试消息中心是否可用"""
        from opspilot.agents import MessageHub, create_message
        
        hub = MessageHub.get_instance()
        assert hub is not None
        
        msg = create_message("test", "hello")
        assert msg is not None
        print("✅ 消息中心可用")


class TestFrameworkStatus:
    """测试框架状态"""
    
    def test_get_framework_status(self):
        """测试获取框架状态"""
        from opspilot import get_framework_status
        
        status = get_framework_status()
        
        print("\n📊 框架状态:")
        for name, available in status.items():
            icon = "✅" if available else "❌"
            print(f"  {icon} {name}: {'可用' if available else '不可用'}")
        
        # 至少有一个框架应该可用
        assert any(status.values())


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self):
        """测试端到端流程"""
        from opspilot.memory import LongTermMemory, ShortTermMemory
        from opspilot.agents import MessageHub
        
        # 1. 初始化记忆
        ltm = LongTermMemory()
        stm = ShortTermMemory()
        
        print(f"长期记忆: {'ChromaDB' if ltm.is_using_chroma else '内存'}")
        print(f"短期记忆: {'Redis' if stm.is_using_redis else '内存'}")
        
        # 2. 存储记忆
        entry = await ltm.memorize("供应商A库存充足")
        assert entry is not None
        
        # 3. 检索记忆
        results = await ltm.recall("供应商库存")
        assert isinstance(results, list)
        
        # 4. 消息中心
        hub = MessageHub.get_instance()
        hub.subscribe("test_agent")
        
        print("✅ 端到端流程测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

