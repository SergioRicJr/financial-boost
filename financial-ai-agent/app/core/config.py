"""
Application Configuration
=========================

Centraliza todas as configurações da aplicação usando Pydantic Settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Financial AI Agent")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/financial_agent.db"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # LLM Configuration
    llm_provider: str = Field(default="openai")
    llm_model: str = Field(default="gpt-4o-mini")
    llm_temperature: float = Field(default=0.7)
    llm_max_tokens: int = Field(default=4096)

    # API Keys
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)

    # Ollama (local)
    ollama_base_url: str = Field(default="http://localhost:11434")

    # Embeddings
    embedding_model: str = Field(default="text-embedding-3-small")

    # Vector Store
    vector_store_type: str = Field(default="chroma")
    vector_store_path: str = Field(default="./data/vectors")
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)

    # LangFuse (Observability)
    langfuse_enabled: bool = Field(default=False)
    langfuse_public_key: Optional[str] = Field(default=None)
    langfuse_secret_key: Optional[str] = Field(default=None)
    langfuse_host: str = Field(default="https://cloud.langfuse.com")

    # Security
    secret_key: str = Field(default="change-me-in-production")
    access_token_expire_minutes: int = Field(default=30)

    # RAG Configuration
    rag_chunk_size: int = Field(default=1000)
    rag_chunk_overlap: int = Field(default=200)
    rag_top_k: int = Field(default=5)

    @property
    def is_production(self) -> bool:
        """Verifica se está em produção."""
        return self.app_env == "production"

    @property
    def litellm_model(self) -> str:
        """Retorna o modelo no formato LiteLLM."""
        if self.llm_provider == "ollama":
            return f"ollama/{self.llm_model}"
        elif self.llm_provider == "anthropic":
            return f"anthropic/{self.llm_model}"
        return self.llm_model  # OpenAI não precisa de prefixo


@lru_cache
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()


# Instância global
settings = get_settings()
