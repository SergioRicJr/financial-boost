"""
Logging Configuration
=====================

Configuração centralizada de logging usando Loguru.
"""

import sys
from typing import Any

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """Configura o sistema de logging."""
    
    # Remove handler padrão
    logger.remove()
    
    # Formato do log
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Handler para console
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
    )
    
    # Handler para arquivo (em produção)
    if settings.is_production:
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            compression="gz",
        )
        
        # Arquivo separado para erros
        logger.add(
            "logs/errors_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="ERROR",
            rotation="1 day",
            retention="90 days",
            compression="gz",
        )
    
    logger.info(f"Logging configurado - Ambiente: {settings.app_env}")


def log_llm_call(
    model: str,
    prompt: str,
    response: str,
    tokens_used: int,
    duration_ms: float,
    **kwargs: Any,
) -> None:
    """Log específico para chamadas LLM."""
    logger.info(
        f"LLM Call | Model: {model} | Tokens: {tokens_used} | "
        f"Duration: {duration_ms:.2f}ms"
    )
    if settings.debug:
        logger.debug(f"Prompt: {prompt[:200]}...")
        logger.debug(f"Response: {response[:200]}...")


def log_agent_action(
    agent_name: str,
    action: str,
    input_data: Any,
    output_data: Any,
) -> None:
    """Log específico para ações de agentes."""
    logger.info(f"Agent: {agent_name} | Action: {action}")
    if settings.debug:
        logger.debug(f"Input: {input_data}")
        logger.debug(f"Output: {output_data}")
