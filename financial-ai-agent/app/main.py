"""
Financial AI Agent - Main Application
=====================================

Ponto de entrada da aplicação FastAPI.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.observability import shutdown_observability, flush_observability
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia ciclo de vida da aplicação.
    
    Executa setup na inicialização e cleanup no encerramento.
    """
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    
    # Configurar logging
    setup_logging()
    
    # Inicializar banco de dados
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Flush observability data
    flush_observability()
    shutdown_observability()
    
    logger.info("Shutdown complete")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    description="""
    ## Financial AI Agent 🤖💰
    
    Um assistente financeiro pessoal inteligente que ajuda você a:
    
    - 📊 **Analisar suas finanças** - Resumos, padrões e insights
    - 💬 **Conversar naturalmente** - Pergunte sobre seus gastos
    - 🎯 **Definir orçamentos** - Limites por categoria
    - 🔮 **Prever gastos** - Projeções baseadas em histórico
    - 📚 **Aprender sobre finanças** - Base de conhecimento integrada
    
    ### Recursos
    
    - **Agentes de IA** com LangGraph
    - **RAG** para conhecimento financeiro
    - **Streaming** de respostas
    - **MCP** para integração externa
    - **Observabilidade** com LangFuse
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(router, prefix="/api/v1")


# Rota raiz
@app.get("/")
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
