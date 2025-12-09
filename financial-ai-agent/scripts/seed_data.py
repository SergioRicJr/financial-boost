"""
Seed Data Script
================

Script para popular o banco de dados com dados de exemplo.
"""

import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal

from app.db.database import init_db, async_session_maker
from app.db.models import UserModel, CategoryModel, TransactionModel
from app.services.category_service import CategoryService


async def create_test_user(session) -> str:
    """Cria usuário de teste."""
    user = UserModel(
        id="test-user-123",
        email="test@example.com",
        hashed_password="hashed_password_here",
        name="Usuário Teste",
    )
    session.add(user)
    await session.flush()
    return user.id


async def create_sample_transactions(session, user_id: str, categories: list):
    """Cria transações de exemplo."""
    
    # Categorias mapeadas
    expense_cats = {c.name: c.id for c in categories if not c.is_income}
    income_cats = {c.name: c.id for c in categories if c.is_income}
    
    # Transações de exemplo
    transactions_data = [
        # Receitas
        ("Salário mensal", 5000, "income", "Salário", 0),
        ("Freelance projeto X", 1500, "income", "Freelance", 5),
        ("Dividendos", 150, "income", "Investimentos", 10),
        
        # Despesas fixas
        ("Aluguel apartamento", 1500, "expense", "Moradia", 1),
        ("Condomínio", 350, "expense", "Moradia", 1),
        ("Conta de luz", 150, "expense", "Moradia", 5),
        ("Internet", 99, "expense", "Moradia", 5),
        ("Plano de saúde", 450, "expense", "Saúde", 1),
        
        # Alimentação
        ("Supermercado Extra", 280, "expense", "Alimentação", 3),
        ("iFood - Jantar", 45, "expense", "Alimentação", 7),
        ("Restaurante almoço", 55, "expense", "Alimentação", 10),
        ("Padaria", 25, "expense", "Alimentação", 12),
        ("iFood - Pizza", 65, "expense", "Alimentação", 15),
        ("Supermercado", 320, "expense", "Alimentação", 17),
        
        # Transporte
        ("Uber - Trabalho", 28, "expense", "Transporte", 2),
        ("Gasolina", 150, "expense", "Transporte", 8),
        ("Uber - Shopping", 35, "expense", "Transporte", 14),
        ("Estacionamento", 20, "expense", "Transporte", 16),
        
        # Lazer
        ("Netflix", 55, "expense", "Lazer", 1),
        ("Spotify", 22, "expense", "Lazer", 1),
        ("Cinema", 60, "expense", "Lazer", 12),
        ("Bar com amigos", 120, "expense", "Lazer", 18),
        
        # Saúde
        ("Farmácia", 85, "expense", "Saúde", 6),
        ("Academia", 99, "expense", "Saúde", 1),
        
        # Educação
        ("Curso online", 150, "expense", "Educação", 4),
        ("Livro técnico", 89, "expense", "Educação", 11),
        
        # Compras
        ("Roupa nova", 180, "expense", "Compras", 9),
        ("Eletrônicos", 350, "expense", "Compras", 20),
    ]
    
    base_date = datetime.utcnow().replace(day=1)
    
    for desc, amount, trans_type, category, days_offset in transactions_data:
        cat_map = income_cats if trans_type == "income" else expense_cats
        category_id = cat_map.get(category)
        
        transaction = TransactionModel(
            user_id=user_id,
            description=desc,
            amount=Decimal(str(amount)),
            type=trans_type,
            category_id=category_id,
            date=base_date + timedelta(days=days_offset),
        )
        session.add(transaction)
    
    await session.flush()
    print(f"Criadas {len(transactions_data)} transações de exemplo")


async def main():
    """Executa o seed."""
    print("Inicializando banco de dados...")
    await init_db()
    
    async with async_session_maker() as session:
        # Criar usuário
        print("Criando usuário de teste...")
        user_id = await create_test_user(session)
        
        # Criar categorias padrão
        print("Criando categorias...")
        category_service = CategoryService(session)
        categories = await category_service.create_default_categories(user_id)
        
        # Criar transações
        print("Criando transações de exemplo...")
        await create_sample_transactions(session, user_id, categories)
        
        await session.commit()
        
    print("\n✅ Seed concluído com sucesso!")
    print(f"   Usuário: test@example.com")
    print(f"   User ID: {user_id}")


if __name__ == "__main__":
    asyncio.run(main())
