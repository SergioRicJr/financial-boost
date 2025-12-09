"""
Analysis Schemas
================

Schemas para análises financeiras geradas pela IA.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SpendingPattern(BaseModel):
    """Padrão de gasto identificado."""
    
    pattern_type: str  # "recurring", "seasonal", "unusual", "trend"
    description: str
    category: Optional[str] = None
    average_amount: Decimal
    frequency: Optional[str] = None  # "daily", "weekly", "monthly"
    confidence: float = Field(..., ge=0, le=1)
    recommendation: Optional[str] = None


class BudgetRecommendation(BaseModel):
    """Recomendação de orçamento."""
    
    category: str
    current_spending: Decimal
    recommended_budget: Decimal
    potential_savings: Decimal
    priority: str = Field(..., pattern=r"^(high|medium|low)$")
    rationale: str
    action_items: list[str]


class FinancialGoal(BaseModel):
    """Meta financeira."""
    
    id: str
    name: str
    target_amount: Decimal
    current_amount: Decimal
    deadline: Optional[datetime] = None
    monthly_contribution_needed: Optional[Decimal] = None
    progress_percentage: float
    status: str = Field(..., pattern=r"^(on_track|at_risk|behind|completed)$")
    tips: list[str]


class FinancialHealth(BaseModel):
    """Saúde financeira geral."""
    
    score: int = Field(..., ge=0, le=100)
    grade: str = Field(..., pattern=r"^(A|B|C|D|F)$")
    
    # Componentes do score
    savings_rate: float
    debt_to_income_ratio: Optional[float] = None
    emergency_fund_months: float
    budget_adherence: float
    
    # Análise
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]


class FinancialSummary(BaseModel):
    """Resumo financeiro completo."""
    
    period_start: datetime
    period_end: datetime
    
    # Totais
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    savings_rate: float
    
    # Por categoria
    expenses_by_category: list[dict]
    income_by_category: list[dict]
    
    # Comparações
    vs_previous_period: dict
    vs_same_period_last_year: Optional[dict] = None
    
    # Top insights
    top_expenses: list[dict]
    unusual_transactions: list[dict]
    
    # Análises IA
    spending_patterns: list[SpendingPattern]
    budget_recommendations: list[BudgetRecommendation]
    financial_health: FinancialHealth
    
    # Narrativa gerada por IA
    ai_summary: str
    ai_tips: list[str]


class PredictionResult(BaseModel):
    """Resultado de previsão financeira."""
    
    prediction_type: str  # "expense", "income", "balance"
    period: str  # "next_month", "next_quarter", "next_year"
    predicted_value: Decimal
    confidence_interval_low: Decimal
    confidence_interval_high: Decimal
    confidence: float = Field(..., ge=0, le=1)
    factors: list[str]
    assumptions: list[str]
