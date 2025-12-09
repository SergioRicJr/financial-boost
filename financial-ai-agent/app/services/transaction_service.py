"""
Transaction Service
===================

Serviço para gerenciamento de transações financeiras.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import TransactionModel, CategoryModel
from app.schemas.transaction import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
    TransactionType,
)


class TransactionService:
    """Serviço de transações."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: str,
        transaction_data: TransactionCreate,
    ) -> Transaction:
        """Cria uma nova transação."""
        transaction = TransactionModel(
            id=str(uuid4()),
            user_id=user_id,
            description=transaction_data.description,
            amount=transaction_data.amount,
            type=transaction_data.type,
            category_id=transaction_data.category_id,
            date=transaction_data.date,
            notes=transaction_data.notes,
            tags=transaction_data.tags,
        )
        
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)
        
        return await self._to_schema(transaction)
    
    async def get_by_id(
        self,
        transaction_id: str,
        user_id: str,
    ) -> Optional[Transaction]:
        """Busca transação por ID."""
        query = (
            select(TransactionModel)
            .options(selectinload(TransactionModel.category))
            .where(
                and_(
                    TransactionModel.id == transaction_id,
                    TransactionModel.user_id == user_id,
                )
            )
        )
        result = await self.db.execute(query)
        transaction = result.scalar_one_or_none()
        
        if transaction:
            return await self._to_schema(transaction)
        return None
    
    async def list_transactions(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category_id: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Lista transações com filtros."""
        query = (
            select(TransactionModel)
            .options(selectinload(TransactionModel.category))
            .where(TransactionModel.user_id == user_id)
        )
        
        if start_date:
            query = query.where(TransactionModel.date >= start_date)
        if end_date:
            query = query.where(TransactionModel.date <= end_date)
        if category_id:
            query = query.where(TransactionModel.category_id == category_id)
        if transaction_type:
            query = query.where(TransactionModel.type == transaction_type)
        
        query = (
            query
            .order_by(TransactionModel.date.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        return [await self._to_schema(t) for t in transactions]
    
    async def update(
        self,
        transaction_id: str,
        user_id: str,
        update_data: TransactionUpdate,
    ) -> Optional[Transaction]:
        """Atualiza uma transação."""
        query = select(TransactionModel).where(
            and_(
                TransactionModel.id == transaction_id,
                TransactionModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(transaction, field, value)
        
        await self.db.flush()
        await self.db.refresh(transaction)
        
        return await self._to_schema(transaction)
    
    async def delete(self, transaction_id: str, user_id: str) -> bool:
        """Remove uma transação."""
        query = select(TransactionModel).where(
            and_(
                TransactionModel.id == transaction_id,
                TransactionModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        transaction = result.scalar_one_or_none()
        
        if transaction:
            await self.db.delete(transaction)
            return True
        return False
    
    async def get_summary(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Retorna resumo das transações."""
        if not start_date:
            start_date = datetime.utcnow().replace(day=1)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Total de receitas
        income_query = select(func.sum(TransactionModel.amount)).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.type == TransactionType.INCOME,
                TransactionModel.date >= start_date,
                TransactionModel.date <= end_date,
            )
        )
        income_result = await self.db.execute(income_query)
        total_income = income_result.scalar() or Decimal("0")
        
        # Total de despesas
        expense_query = select(func.sum(TransactionModel.amount)).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.type == TransactionType.EXPENSE,
                TransactionModel.date >= start_date,
                TransactionModel.date <= end_date,
            )
        )
        expense_result = await self.db.execute(expense_query)
        total_expenses = expense_result.scalar() or Decimal("0")
        
        # Gastos por categoria
        by_category_query = (
            select(
                CategoryModel.name,
                func.sum(TransactionModel.amount).label("total"),
                func.count(TransactionModel.id).label("count"),
            )
            .join(CategoryModel, TransactionModel.category_id == CategoryModel.id)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.type == TransactionType.EXPENSE,
                    TransactionModel.date >= start_date,
                    TransactionModel.date <= end_date,
                )
            )
            .group_by(CategoryModel.name)
            .order_by(func.sum(TransactionModel.amount).desc())
        )
        by_category_result = await self.db.execute(by_category_query)
        expenses_by_category = [
            {"category": row.name, "total": float(row.total), "count": row.count}
            for row in by_category_result
        ]
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_balance": float(total_income - total_expenses),
            "savings_rate": (
                float((total_income - total_expenses) / total_income * 100)
                if total_income > 0
                else 0
            ),
            "expenses_by_category": expenses_by_category,
        }
    
    async def get_transactions_for_analysis(
        self,
        user_id: str,
        days: int = 90,
    ) -> list[dict]:
        """Retorna transações formatadas para análise pela IA."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        transactions = await self.list_transactions(
            user_id=user_id,
            start_date=start_date,
            limit=1000,
        )
        
        return [
            {
                "id": t.id,
                "description": t.description,
                "amount": float(t.amount),
                "type": t.type,
                "category": t.category_name,
                "date": t.date.isoformat(),
                "tags": t.tags,
            }
            for t in transactions
        ]
    
    async def _to_schema(self, model: TransactionModel) -> Transaction:
        """Converte modelo para schema."""
        return Transaction(
            id=model.id,
            user_id=model.user_id,
            description=model.description,
            amount=model.amount,
            type=model.type,
            category_id=model.category_id,
            category_name=model.category.name if model.category else None,
            date=model.date,
            notes=model.notes,
            tags=model.tags or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
