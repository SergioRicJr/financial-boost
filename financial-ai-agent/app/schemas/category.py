"""
Category Schemas
================

Schemas para categorias de transações.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    """Base schema para categorias."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    budget_limit: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_income: bool = False


class CategoryCreate(CategoryBase):
    """Schema para criação de categoria."""
    pass


class CategoryUpdate(BaseModel):
    """Schema para atualização de categoria."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    budget_limit: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_income: Optional[bool] = None


class Category(CategoryBase):
    """Schema completo de categoria."""
    
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CategorySummary(BaseModel):
    """Resumo de gastos por categoria."""
    
    category_id: str
    category_name: str
    total_amount: Decimal
    transaction_count: int
    percentage_of_total: float
    budget_limit: Optional[Decimal] = None
    budget_used_percentage: Optional[float] = None
    trend: str = Field(..., pattern=r"^(up|down|stable)$")
    month_over_month_change: float
