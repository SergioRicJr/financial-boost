"""
API Dependencies
================

Dependências injetáveis para os endpoints da API.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.config import settings


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Obtém o usuário atual do token de autorização.
    
    Para simplificação, retorna um user_id fixo em desenvolvimento.
    Em produção, validaria o JWT token.
    """
    if settings.debug:
        # Em desenvolvimento, usar usuário de teste
        return "test-user-123"
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    
    # TODO: Implementar validação JWT real
    # token = authorization.replace("Bearer ", "")
    # payload = decode_jwt(token)
    # return payload["user_id"]
    
    return "user-from-token"


async def get_db_session() -> AsyncSession:
    """Obtém sessão do banco de dados."""
    async for session in get_db():
        yield session
