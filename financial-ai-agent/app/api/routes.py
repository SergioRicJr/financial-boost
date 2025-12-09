"""
API Routes
==========

Definição das rotas da API.
"""

import json
import time
from typing import Any, AsyncIterator, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db_session
from app.agents.financial_agent import FinancialAgent
from app.core.observability import trace_operation, Tracer
from app.mcp.server import MCPServer
from app.rag.retriever import FinancialRetriever
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage, MessageRole, StreamChunk


router = APIRouter()


# ============================================
# Health Check
# ============================================

@router.get("/health")
async def health_check():
    """Verifica saúde da aplicação."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
    }


# ============================================
# Chat Endpoints
# ============================================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Endpoint principal de chat com o assistente financeiro.
    
    Processa a mensagem do usuário através do agente de IA
    e retorna a resposta.
    """
    start_time = time.time()
    conversation_id = request.conversation_id or str(uuid4())
    
    async with trace_operation(
        "chat",
        user_id=user_id,
        input_data={"message": request.message},
    ) as tracer:
        try:
            # Criar agente
            agent = FinancialAgent(
                user_id=user_id,
                conversation_id=conversation_id,
                context=request.context,
            )
            
            # Processar mensagem
            response_text = await agent.chat(request.message)
            
            processing_time = (time.time() - start_time) * 1000
            
            return ChatResponse(
                conversation_id=conversation_id,
                message=ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=response_text,
                ),
                tool_calls=[],
                sources=[],
                tokens_used=0,  # TODO: Calcular tokens reais
                processing_time_ms=processing_time,
                model_used="gpt-4o-mini",
            )
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Endpoint de chat com streaming de resposta.
    
    Retorna a resposta em chunks via Server-Sent Events (SSE).
    """
    conversation_id = request.conversation_id or str(uuid4())
    
    async def generate_stream() -> AsyncIterator[str]:
        """Gera stream de eventos SSE."""
        try:
            agent = FinancialAgent(
                user_id=user_id,
                conversation_id=conversation_id,
                context=request.context,
            )
            
            # Evento de início
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\n\n"
            
            # Stream de chunks
            async for chunk in agent.chat_stream(request.message):
                chunk_data = StreamChunk(
                    conversation_id=conversation_id,
                    chunk_type="text",
                    content=chunk,
                )
                yield f"data: {chunk_data.model_dump_json()}\n\n"
            
            # Evento de fim
            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_data = {
                "type": "error",
                "conversation_id": conversation_id,
                "error": str(e),
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================
# RAG Endpoints
# ============================================

@router.post("/rag/query")
async def rag_query(
    question: str,
    top_k: int = 5,
    user_id: str = Depends(get_current_user),
):
    """
    Consulta a base de conhecimento financeiro.
    
    Usa RAG para encontrar informações relevantes e gerar resposta.
    """
    try:
        retriever = FinancialRetriever(user_id=user_id)
        result = await retriever.query_with_context(question, top_k=top_k)
        
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "tokens_used": result["tokens_used"],
        }
        
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/rag/documents")
async def add_document(
    content: str,
    metadata: Optional[dict] = None,
    user_id: str = Depends(get_current_user),
):
    """
    Adiciona documento à base de conhecimento.
    """
    try:
        retriever = FinancialRetriever(user_id=user_id)
        num_chunks = await retriever.add_document(content, metadata)
        
        return {
            "success": True,
            "chunks_created": num_chunks,
        }
        
    except Exception as e:
        logger.error(f"Add document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================
# MCP Endpoints
# ============================================

@router.post("/mcp/message")
async def mcp_message(
    message: dict,
    user_id: str = Depends(get_current_user),
):
    """
    Endpoint para mensagens MCP (Model Context Protocol).
    
    Permite que clientes MCP interajam com as ferramentas financeiras.
    """
    try:
        server = MCPServer(context={"user_id": user_id})
        response = await server.handle_message(message)
        return response
        
    except Exception as e:
        logger.error(f"MCP error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32603,
                "message": str(e),
            },
        }


@router.get("/mcp/tools")
async def list_mcp_tools():
    """Lista ferramentas MCP disponíveis."""
    server = MCPServer()
    return await server.list_tools()


# ============================================
# Analysis Endpoints
# ============================================

@router.get("/analysis/summary")
async def get_financial_summary(
    period: str = "month",
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retorna resumo financeiro do período.
    """
    from app.services.transaction_service import TransactionService
    
    try:
        service = TransactionService(db)
        summary = await service.get_summary(user_id=user_id)
        return summary
        
    except Exception as e:
        logger.error(f"Summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/analysis/health")
async def get_financial_health(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retorna análise de saúde financeira.
    """
    from app.services.analysis_service import AnalysisService
    
    try:
        service = AnalysisService(db)
        health = await service.calculate_financial_health(user_id=user_id)
        return health.model_dump()
        
    except Exception as e:
        logger.error(f"Health analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/analysis/patterns")
async def get_spending_patterns(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Identifica padrões de gastos.
    """
    from app.services.analysis_service import AnalysisService
    
    try:
        service = AnalysisService(db)
        patterns = await service.identify_spending_patterns(user_id=user_id)
        return [p.model_dump() for p in patterns]
        
    except Exception as e:
        logger.error(f"Patterns analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================
# Transaction Endpoints
# ============================================

@router.get("/transactions")
async def list_transactions(
    limit: int = 10,
    offset: int = 0,
    category_id: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Lista transações do usuário."""
    from app.services.transaction_service import TransactionService
    
    try:
        service = TransactionService(db)
        transactions = await service.list_transactions(
            user_id=user_id,
            category_id=category_id,
            limit=limit,
            offset=offset,
        )
        return [t.model_dump() for t in transactions]
        
    except Exception as e:
        logger.error(f"List transactions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/transactions")
async def create_transaction(
    description: str,
    amount: float,
    transaction_type: str,
    category_id: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Cria nova transação."""
    from app.services.transaction_service import TransactionService
    from app.schemas.transaction import TransactionCreate, TransactionType
    
    try:
        service = TransactionService(db)
        
        transaction_data = TransactionCreate(
            description=description,
            amount=amount,
            type=TransactionType(transaction_type),
            category_id=category_id,
        )
        
        transaction = await service.create(
            user_id=user_id,
            transaction_data=transaction_data,
        )
        
        return transaction.model_dump()
        
    except Exception as e:
        logger.error(f"Create transaction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================
# Category Endpoints
# ============================================

@router.get("/categories")
async def list_categories(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Lista categorias do usuário."""
    from app.services.category_service import CategoryService
    
    try:
        service = CategoryService(db)
        categories = await service.list_categories(user_id=user_id)
        return [c.model_dump() for c in categories]
        
    except Exception as e:
        logger.error(f"List categories error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
