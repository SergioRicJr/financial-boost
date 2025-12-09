"""
Chat Schemas
============

Schemas para o chat com o assistente financeiro.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Papéis das mensagens no chat."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """Mensagem do chat."""
    
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # Para mensagens de tool
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    """Requisição de chat."""
    
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    stream: bool = False
    
    # Opções avançadas
    include_sources: bool = True
    max_tokens: Optional[int] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)


class ToolCall(BaseModel):
    """Chamada de ferramenta pelo agente."""
    
    id: str
    name: str
    arguments: dict[str, Any]
    result: Optional[Any] = None


class ChatResponse(BaseModel):
    """Resposta do chat."""
    
    conversation_id: str
    message: ChatMessage
    tool_calls: list[ToolCall] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    
    # Metadados
    tokens_used: int
    processing_time_ms: float
    model_used: str


class StreamChunk(BaseModel):
    """Chunk para streaming de resposta."""
    
    conversation_id: str
    chunk_type: str = Field(..., pattern=r"^(text|tool_start|tool_end|done|error)$")
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # Para tool calls
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None


class ConversationHistory(BaseModel):
    """Histórico de conversa."""
    
    id: str
    user_id: str
    title: Optional[str] = None
    messages: list[ChatMessage]
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
