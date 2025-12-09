"""
Pytest Configuration
====================

Fixtures e configurações compartilhadas para testes.
"""

import asyncio
import os
import pytest
from typing import AsyncGenerator

# Configurar variáveis de ambiente para testes
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["LANGFUSE_ENABLED"] = "false"


@pytest.fixture(scope="session")
def event_loop():
    """Cria event loop para testes assíncronos."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator:
    """Fixture para sessão de banco de dados de teste."""
    from app.db.database import async_session_maker, init_db, engine, Base
    
    # Criar tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Criar sessão
    async with async_session_maker() as session:
        yield session
    
    # Limpar tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_user_id() -> str:
    """Fixture para ID de usuário de teste."""
    return "test-user-123"


@pytest.fixture
def sample_transactions() -> list[dict]:
    """Fixture com transações de exemplo."""
    return [
        {
            "description": "Salário",
            "amount": 5000.0,
            "type": "income",
            "category": "Salário",
        },
        {
            "description": "Aluguel",
            "amount": 1500.0,
            "type": "expense",
            "category": "Moradia",
        },
        {
            "description": "Supermercado",
            "amount": 450.0,
            "type": "expense",
            "category": "Alimentação",
        },
        {
            "description": "Uber",
            "amount": 85.0,
            "type": "expense",
            "category": "Transporte",
        },
        {
            "description": "Netflix",
            "amount": 55.0,
            "type": "expense",
            "category": "Lazer",
        },
    ]
