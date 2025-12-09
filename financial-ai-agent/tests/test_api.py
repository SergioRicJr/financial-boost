"""
Tests for API
=============

Testes para os endpoints da API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


class TestHealthEndpoint:
    """Testes para o endpoint de health check."""
    
    @pytest.fixture
    def client(self):
        """Fixture para criar cliente de teste."""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Testa endpoint de health check."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestRootEndpoint:
    """Testes para o endpoint raiz."""
    
    @pytest.fixture
    def client(self):
        """Fixture para criar cliente de teste."""
        return TestClient(app)
    
    def test_root(self, client):
        """Testa endpoint raiz."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"


class TestMCPEndpoint:
    """Testes para os endpoints MCP."""
    
    @pytest.fixture
    def client(self):
        """Fixture para criar cliente de teste."""
        return TestClient(app)
    
    def test_list_mcp_tools(self, client):
        """Testa listagem de ferramentas MCP."""
        response = client.get("/api/v1/mcp/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) > 0
    
    def test_mcp_message_list_tools(self, client):
        """Testa mensagem MCP para listar ferramentas."""
        message = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/list",
            "params": {},
        }
        
        response = client.post("/api/v1/mcp/message", json=message)
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tools" in data["result"]


class TestChatEndpoint:
    """Testes para os endpoints de chat."""
    
    @pytest.fixture
    def client(self):
        """Fixture para criar cliente de teste."""
        return TestClient(app)
    
    @patch("app.api.routes.FinancialAgent")
    def test_chat(self, mock_agent_class, client):
        """Testa endpoint de chat."""
        # Configurar mock
        mock_agent = AsyncMock()
        mock_agent.chat.return_value = "Resposta de teste"
        mock_agent_class.return_value = mock_agent
        
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Olá",
                "stream": False,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "message" in data
