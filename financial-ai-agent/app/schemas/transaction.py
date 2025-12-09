"""
Transaction Schemas
===================

Schemas para transações financeiras.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TransactionType(str, Enum):
    """Tipos de transação."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    INVESTMENT = "investment"


class TransactionBase(BaseModel):
    """Base schema para transações."""
    
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    type: TransactionType
    category_id: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(None, max_length=1000)
    tags: list[str] = Field(default_factory=list)
    
    model_config = ConfigDict(use_enum_values=True)


class TransactionCreate(TransactionBase):
    """Schema para criação de transação."""
    pass


class TransactionUpdate(BaseModel):
    """Schema para atualização de transação."""
    
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    type: Optional[TransactionType] = None
    category_id: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    tags: Optional[list[str]] = None
    
    model_config = ConfigDict(use_enum_values=True)


class Transaction(TransactionBase):
    """Schema completo de transação."""
    
    id: str
    user_id: str
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TransactionAnalysis(BaseModel):
    """Análise de uma transação pela IA."""
    
    transaction_id: str
    suggested_category: str
    confidence: float = Field(..., ge=0, le=1)
    insights: list[str]
    similar_transactions: list[str]
    is_recurring: bool
    recurring_pattern: Optional[str] = None
