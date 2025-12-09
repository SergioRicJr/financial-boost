"""
Tests for Financial Agent
=========================

Testes para o agente financeiro.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.financial_agent import FinancialAgent
from app.agents.tools import FinancialTools


class TestFinancialTools:
    """Testes para as ferramentas financeiras."""
    
    @pytest.fixture
    def tools(self):
        """Fixture para criar instância de tools."""
        return FinancialTools({"user_id": "test-user"})
    
    @pytest.mark.asyncio
    async def test_create_transaction(self, tools):
        """Testa criação de transação."""
        result = await tools.create_transaction(
            description="Test transaction",
            amount=100.0,
            transaction_type="expense",
            category="Alimentação",
        )
        
        assert "✅" in result
        assert "Test transaction" in result
        assert "100" in result
    
    @pytest.mark.asyncio
    async def test_get_transactions(self, tools):
        """Testa listagem de transações."""
        result = await tools.get_transactions(limit=5)
        
        assert "Transações" in result
    
    @pytest.mark.asyncio
    async def test_get_financial_summary(self, tools):
        """Testa resumo financeiro."""
        result = await tools.get_financial_summary(period="month")
        
        assert "Resumo Financeiro" in result
        assert "Receitas" in result
        assert "Despesas" in result
    
    @pytest.mark.asyncio
    async def test_analyze_finances_health(self, tools):
        """Testa análise de saúde financeira."""
        result = await tools.analyze_finances(analysis_type="health")
        
        assert "Saúde Financeira" in result
        assert "Score" in result
    
    @pytest.mark.asyncio
    async def test_analyze_finances_patterns(self, tools):
        """Testa identificação de padrões."""
        result = await tools.analyze_finances(analysis_type="patterns")
        
        assert "Padrões" in result
    
    @pytest.mark.asyncio
    async def test_categorize_transaction(self, tools):
        """Testa categorização automática."""
        result = await tools.categorize_transaction(
            description="Almoço restaurante",
            amount=50.0,
        )
        
        assert "Categoria" in result
    
    @pytest.mark.asyncio
    async def test_set_budget(self, tools):
        """Testa definição de orçamento."""
        result = await tools.set_budget(
            category="Alimentação",
            amount=800.0,
        )
        
        assert "Orçamento" in result
        assert "800" in result


class TestFinancialAgent:
    """Testes para o agente financeiro."""
    
    @pytest.fixture
    def agent(self):
        """Fixture para criar agente."""
        return FinancialAgent(
            user_id="test-user",
            conversation_id="test-conversation",
        )
    
    def test_agent_initialization(self, agent):
        """Testa inicialização do agente."""
        assert agent.user_id == "test-user"
        assert agent.conversation_id == "test-conversation"
        assert agent.llm is not None
        assert agent.tools is not None
    
    def test_agent_has_tools(self, agent):
        """Testa que o agente tem ferramentas configuradas."""
        tools_schema = agent._get_tools_schema()
        
        assert len(tools_schema) > 0
        
        tool_names = [t["function"]["name"] for t in tools_schema]
        assert "create_transaction" in tool_names
        assert "get_financial_summary" in tool_names
        assert "analyze_finances" in tool_names
    
    @pytest.mark.asyncio
    async def test_format_messages(self, agent):
        """Testa formatação de mensagens."""
        from langchain_core.messages import HumanMessage, AIMessage
        
        messages = [
            HumanMessage(content="Olá"),
            AIMessage(content="Oi! Como posso ajudar?"),
        ]
        
        formatted = agent._format_messages(messages)
        
        # Deve ter system prompt + 2 mensagens
        assert len(formatted) == 3
        assert formatted[0]["role"] == "system"
        assert formatted[1]["role"] == "user"
        assert formatted[2]["role"] == "assistant"
