"""
Observability
=============

Configuração de observabilidade com LangFuse e OpenTelemetry.
Permite rastrear e monitorar chamadas LLM, agentes e RAG.
"""

import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable, Optional
from uuid import uuid4

from loguru import logger

from app.core.config import settings


# Variável global para o cliente LangFuse
_langfuse_client = None


def get_langfuse():
    """Retorna cliente LangFuse (lazy initialization)."""
    global _langfuse_client
    
    if not settings.langfuse_enabled:
        return None
    
    if _langfuse_client is None:
        try:
            from langfuse import Langfuse
            
            _langfuse_client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
            logger.info("LangFuse client initialized")
        except ImportError:
            logger.warning("LangFuse not installed. Observability disabled.")
            return None
        except Exception as e:
            logger.warning(f"Failed to initialize LangFuse: {e}")
            return None
    
    return _langfuse_client


class Tracer:
    """
    Tracer para observabilidade de operações.
    
    Integra com LangFuse para rastrear:
    - Chamadas LLM
    - Execução de agentes
    - Pipeline RAG
    - Uso de ferramentas
    """
    
    def __init__(
        self,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        self.name = name
        self.user_id = user_id
        self.session_id = session_id or str(uuid4())
        self.metadata = metadata or {}
        self.langfuse = get_langfuse()
        self._trace = None
        self._spans = {}
    
    def start_trace(self, input_data: Any = None) -> "Tracer":
        """Inicia um trace."""
        if self.langfuse:
            try:
                self._trace = self.langfuse.trace(
                    name=self.name,
                    user_id=self.user_id,
                    session_id=self.session_id,
                    metadata=self.metadata,
                    input=input_data,
                )
            except Exception as e:
                logger.warning(f"Failed to create trace: {e}")
        
        return self
    
    def end_trace(self, output_data: Any = None) -> None:
        """Finaliza o trace."""
        if self._trace:
            try:
                self._trace.update(output=output_data)
            except Exception as e:
                logger.warning(f"Failed to end trace: {e}")
    
    def start_span(
        self,
        name: str,
        span_type: str = "span",
        input_data: Any = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Inicia um span dentro do trace.
        
        Args:
            name: Nome do span
            span_type: Tipo (span, generation, retrieval)
            input_data: Dados de entrada
            metadata: Metadados adicionais
            
        Returns:
            ID do span
        """
        span_id = str(uuid4())
        
        if self._trace:
            try:
                if span_type == "generation":
                    span = self._trace.generation(
                        name=name,
                        input=input_data,
                        metadata=metadata,
                    )
                elif span_type == "retrieval":
                    span = self._trace.span(
                        name=name,
                        input=input_data,
                        metadata={**(metadata or {}), "type": "retrieval"},
                    )
                else:
                    span = self._trace.span(
                        name=name,
                        input=input_data,
                        metadata=metadata,
                    )
                
                self._spans[span_id] = {
                    "span": span,
                    "start_time": time.time(),
                    "type": span_type,
                }
            except Exception as e:
                logger.warning(f"Failed to create span: {e}")
        
        return span_id
    
    def end_span(
        self,
        span_id: str,
        output_data: Any = None,
        metadata: Optional[dict] = None,
        usage: Optional[dict] = None,
    ) -> None:
        """
        Finaliza um span.
        
        Args:
            span_id: ID do span
            output_data: Dados de saída
            metadata: Metadados adicionais
            usage: Informações de uso (tokens, etc.)
        """
        if span_id in self._spans:
            span_info = self._spans[span_id]
            
            if span_info["span"]:
                try:
                    update_data = {"output": output_data}
                    
                    if metadata:
                        update_data["metadata"] = metadata
                    
                    if usage and span_info["type"] == "generation":
                        update_data["usage"] = usage
                    
                    span_info["span"].end(**update_data)
                except Exception as e:
                    logger.warning(f"Failed to end span: {e}")
            
            del self._spans[span_id]
    
    def log_llm_call(
        self,
        model: str,
        messages: list[dict],
        response: str,
        usage: Optional[dict] = None,
        duration_ms: Optional[float] = None,
    ) -> None:
        """
        Registra uma chamada LLM.
        
        Args:
            model: Nome do modelo
            messages: Mensagens enviadas
            response: Resposta recebida
            usage: Tokens utilizados
            duration_ms: Duração em ms
        """
        if self._trace:
            try:
                self._trace.generation(
                    name="llm_call",
                    model=model,
                    input=messages,
                    output=response,
                    usage=usage,
                    metadata={"duration_ms": duration_ms} if duration_ms else None,
                )
            except Exception as e:
                logger.warning(f"Failed to log LLM call: {e}")
    
    def log_tool_call(
        self,
        tool_name: str,
        input_data: Any,
        output_data: Any,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """Registra uma chamada de ferramenta."""
        if self._trace:
            try:
                self._trace.span(
                    name=f"tool:{tool_name}",
                    input=input_data,
                    output=output_data,
                    metadata={
                        "duration_ms": duration_ms,
                        "error": error,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to log tool call: {e}")
    
    def log_retrieval(
        self,
        query: str,
        documents: list[dict],
        duration_ms: Optional[float] = None,
    ) -> None:
        """Registra uma operação de retrieval."""
        if self._trace:
            try:
                self._trace.span(
                    name="retrieval",
                    input=query,
                    output=documents,
                    metadata={
                        "type": "retrieval",
                        "num_documents": len(documents),
                        "duration_ms": duration_ms,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to log retrieval: {e}")
    
    def set_score(
        self,
        name: str,
        value: float,
        comment: Optional[str] = None,
    ) -> None:
        """
        Define um score para o trace.
        
        Útil para avaliar qualidade das respostas.
        """
        if self._trace:
            try:
                self._trace.score(
                    name=name,
                    value=value,
                    comment=comment,
                )
            except Exception as e:
                logger.warning(f"Failed to set score: {e}")


@asynccontextmanager
async def trace_operation(
    name: str,
    user_id: Optional[str] = None,
    input_data: Any = None,
    metadata: Optional[dict] = None,
):
    """
    Context manager para tracing de operações.
    
    Usage:
        async with trace_operation("chat", user_id="123") as tracer:
            tracer.log_llm_call(...)
            result = await do_something()
    """
    tracer = Tracer(name=name, user_id=user_id, metadata=metadata)
    tracer.start_trace(input_data)
    
    try:
        yield tracer
    finally:
        tracer.end_trace()


def trace_function(name: Optional[str] = None):
    """
    Decorator para adicionar tracing a funções.
    
    Usage:
        @trace_function("my_operation")
        async def my_function(x, y):
            return x + y
    """
    def decorator(func: Callable):
        operation_name = name or func.__name__
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with trace_operation(operation_name) as tracer:
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    tracer.end_trace({
                        "success": True,
                        "duration_ms": duration_ms,
                    })
                    
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    tracer.end_trace({
                        "success": False,
                        "error": str(e),
                        "duration_ms": duration_ms,
                    })
                    
                    raise
        
        return wrapper
    
    return decorator


class PromptManager:
    """
    Gerenciador de prompts com versionamento via LangFuse.
    
    Permite:
    - Versionamento de prompts
    - A/B testing
    - Métricas de desempenho por versão
    """
    
    def __init__(self):
        self.langfuse = get_langfuse()
        self._cache = {}
    
    def get_prompt(
        self,
        name: str,
        version: Optional[int] = None,
        variables: Optional[dict] = None,
    ) -> str:
        """
        Obtém um prompt do LangFuse.
        
        Args:
            name: Nome do prompt
            version: Versão específica (None = latest)
            variables: Variáveis para interpolação
            
        Returns:
            Prompt compilado
        """
        if not self.langfuse:
            return self._get_fallback_prompt(name, variables)
        
        try:
            cache_key = f"{name}:{version or 'latest'}"
            
            if cache_key not in self._cache:
                prompt = self.langfuse.get_prompt(name, version=version)
                self._cache[cache_key] = prompt
            else:
                prompt = self._cache[cache_key]
            
            if variables:
                return prompt.compile(**variables)
            
            return prompt.prompt
            
        except Exception as e:
            logger.warning(f"Failed to get prompt from LangFuse: {e}")
            return self._get_fallback_prompt(name, variables)
    
    def _get_fallback_prompt(
        self,
        name: str,
        variables: Optional[dict] = None,
    ) -> str:
        """Retorna prompt fallback quando LangFuse não está disponível."""
        
        fallback_prompts = {
            "financial_assistant": """Você é um assistente financeiro pessoal.
Ajude o usuário a gerenciar suas finanças de forma clara e amigável.
{context}""",
            
            "categorization": """Categorize a transação: {description}
Valor: R$ {amount}
Escolha entre: {categories}""",
            
            "analysis": """Analise os dados financeiros:
{data}
Forneça insights úteis e recomendações práticas.""",
        }
        
        template = fallback_prompts.get(name, "")
        
        if variables and template:
            try:
                return template.format(**variables)
            except KeyError:
                return template
        
        return template
    
    def create_prompt(
        self,
        name: str,
        prompt: str,
        labels: Optional[list[str]] = None,
    ) -> None:
        """
        Cria ou atualiza um prompt no LangFuse.
        
        Args:
            name: Nome do prompt
            prompt: Conteúdo do prompt
            labels: Labels para organização
        """
        if not self.langfuse:
            logger.warning("LangFuse not available. Prompt not saved.")
            return
        
        try:
            self.langfuse.create_prompt(
                name=name,
                prompt=prompt,
                labels=labels or [],
            )
            
            # Invalidar cache
            for key in list(self._cache.keys()):
                if key.startswith(f"{name}:"):
                    del self._cache[key]
                    
        except Exception as e:
            logger.error(f"Failed to create prompt: {e}")


# Instâncias globais
prompt_manager = PromptManager()


def flush_observability():
    """Força envio de dados pendentes para LangFuse."""
    langfuse = get_langfuse()
    if langfuse:
        try:
            langfuse.flush()
        except Exception as e:
            logger.warning(f"Failed to flush LangFuse: {e}")


def shutdown_observability():
    """Encerra conexões de observabilidade."""
    global _langfuse_client
    
    if _langfuse_client:
        try:
            _langfuse_client.flush()
            _langfuse_client.shutdown()
        except Exception as e:
            logger.warning(f"Failed to shutdown LangFuse: {e}")
        finally:
            _langfuse_client = None
