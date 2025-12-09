"""Schemas module - Pydantic models for data validation."""

from app.schemas.transaction import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
    TransactionType,
    TransactionAnalysis,
)
from app.schemas.category import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    CategorySummary,
)
from app.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    StreamChunk,
    MessageRole,
)
from app.schemas.analysis import (
    FinancialSummary,
    SpendingPattern,
    BudgetRecommendation,
    FinancialGoal,
    FinancialHealth,
)

__all__ = [
    # Transaction
    "Transaction",
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionType",
    "TransactionAnalysis",
    # Category
    "Category",
    "CategoryCreate",
    "CategoryUpdate",
    "CategorySummary",
    # Chat
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "StreamChunk",
    "MessageRole",
    # Analysis
    "FinancialSummary",
    "SpendingPattern",
    "BudgetRecommendation",
    "FinancialGoal",
    "FinancialHealth",
]
