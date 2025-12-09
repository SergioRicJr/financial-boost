"""
LLM Service
===========

Serviço para interação com LLMs via LiteLLM.
Suporta múltiplos providers e observabilidade.
"""

import time
from typing import Any, AsyncIterator, Optional

import litellm
from litellm import acompletion
from loguru import logger

from app.core.config import settings


# Configurar LiteLLM
litellm.set_verbose = settings.debug


class LLMService:
    """Serviço de LLM com suporte a múltiplos providers."""
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        self.model = model or settings.litellm_model
        self.temperature = temperature or settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens
        
        # Configurar API keys
        if settings.openai_api_key:
            litellm.api_key = settings.openai_api_key
    
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        """
        Executa uma completion com o LLM.
        
        Args:
            messages: Lista de mensagens no formato OpenAI
            temperature: Temperatura para geração
            max_tokens: Máximo de tokens na resposta
            tools: Lista de ferramentas disponíveis
            tool_choice: Estratégia de escolha de ferramentas
            
        Returns:
            Resposta do LLM
        """
        start_time = time.time()
        
        try:
            response = await acompletion(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                tools=tools,
                tool_choice=tool_choice,
                **kwargs,
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"LLM completion | Model: {self.model} | "
                f"Duration: {duration_ms:.2f}ms | "
                f"Tokens: {response.usage.total_tokens if response.usage else 'N/A'}"
            )
            
            return {
                "content": response.choices[0].message.content,
                "tool_calls": (
                    response.choices[0].message.tool_calls
                    if hasattr(response.choices[0].message, "tool_calls")
                    else None
                ),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                "model": self.model,
                "duration_ms": duration_ms,
            }
            
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            raise
    
    async def stream_complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Executa completion com streaming.
        
        Yields:
            Chunks de texto da resposta
        """
        try:
            response = await acompletion(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
                **kwargs,
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"LLM streaming error: {str(e)}")
            raise
    
    async def embed(self, text: str) -> list[float]:
        """
        Gera embeddings para um texto.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Vetor de embeddings
        """
        try:
            response = await litellm.aembedding(
                model=settings.embedding_model,
                input=[text],
            )
            return response.data[0]["embedding"]
            
        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            raise
    
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Gera embeddings para múltiplos textos.
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de vetores de embeddings
        """
        try:
            response = await litellm.aembedding(
                model=settings.embedding_model,
                input=texts,
            )
            return [item["embedding"] for item in response.data]
            
        except Exception as e:
            logger.error(f"Batch embedding error: {str(e)}")
            raise


# Instância global para reuso
llm_service = LLMService()
