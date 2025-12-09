"""
Category Service
================

Serviço para gerenciamento de categorias.
"""

from typing import Optional
from uuid import uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CategoryModel
from app.schemas.category import Category, CategoryCreate, CategoryUpdate


# Categorias padrão para novos usuários
DEFAULT_CATEGORIES = [
    {"name": "Alimentação", "icon": "🍽️", "color": "#FF6B6B", "is_income": False},
    {"name": "Transporte", "icon": "🚗", "color": "#4ECDC4", "is_income": False},
    {"name": "Moradia", "icon": "🏠", "color": "#45B7D1", "is_income": False},
    {"name": "Saúde", "icon": "🏥", "color": "#96CEB4", "is_income": False},
    {"name": "Educação", "icon": "📚", "color": "#FFEAA7", "is_income": False},
    {"name": "Lazer", "icon": "🎮", "color": "#DDA0DD", "is_income": False},
    {"name": "Compras", "icon": "🛒", "color": "#98D8C8", "is_income": False},
    {"name": "Serviços", "icon": "💡", "color": "#F7DC6F", "is_income": False},
    {"name": "Investimentos", "icon": "📈", "color": "#82E0AA", "is_income": False},
    {"name": "Outros", "icon": "📦", "color": "#AEB6BF", "is_income": False},
    {"name": "Salário", "icon": "💰", "color": "#58D68D", "is_income": True},
    {"name": "Freelance", "icon": "💻", "color": "#5DADE2", "is_income": True},
    {"name": "Investimentos", "icon": "📊", "color": "#AF7AC5", "is_income": True},
    {"name": "Outros Rendimentos", "icon": "💵", "color": "#F8C471", "is_income": True},
]


class CategoryService:
    """Serviço de categorias."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: str,
        category_data: CategoryCreate,
    ) -> Category:
        """Cria uma nova categoria."""
        category = CategoryModel(
            id=str(uuid4()),
            user_id=user_id,
            name=category_data.name,
            description=category_data.description,
            icon=category_data.icon,
            color=category_data.color,
            budget_limit=category_data.budget_limit,
            is_income=category_data.is_income,
        )
        
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        
        return self._to_schema(category)
    
    async def create_default_categories(self, user_id: str) -> list[Category]:
        """Cria categorias padrão para um novo usuário."""
        categories = []
        
        for cat_data in DEFAULT_CATEGORIES:
            category = CategoryModel(
                id=str(uuid4()),
                user_id=user_id,
                **cat_data,
            )
            self.db.add(category)
            categories.append(category)
        
        await self.db.flush()
        
        return [self._to_schema(c) for c in categories]
    
    async def get_by_id(
        self,
        category_id: str,
        user_id: str,
    ) -> Optional[Category]:
        """Busca categoria por ID."""
        query = select(CategoryModel).where(
            and_(
                CategoryModel.id == category_id,
                CategoryModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()
        
        if category:
            return self._to_schema(category)
        return None
    
    async def get_by_name(
        self,
        name: str,
        user_id: str,
    ) -> Optional[Category]:
        """Busca categoria por nome."""
        query = select(CategoryModel).where(
            and_(
                CategoryModel.name.ilike(name),
                CategoryModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()
        
        if category:
            return self._to_schema(category)
        return None
    
    async def list_categories(
        self,
        user_id: str,
        is_income: Optional[bool] = None,
    ) -> list[Category]:
        """Lista todas as categorias do usuário."""
        query = select(CategoryModel).where(CategoryModel.user_id == user_id)
        
        if is_income is not None:
            query = query.where(CategoryModel.is_income == is_income)
        
        query = query.order_by(CategoryModel.name)
        
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        return [self._to_schema(c) for c in categories]
    
    async def update(
        self,
        category_id: str,
        user_id: str,
        update_data: CategoryUpdate,
    ) -> Optional[Category]:
        """Atualiza uma categoria."""
        query = select(CategoryModel).where(
            and_(
                CategoryModel.id == category_id,
                CategoryModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()
        
        if not category:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(category, field, value)
        
        await self.db.flush()
        await self.db.refresh(category)
        
        return self._to_schema(category)
    
    async def delete(self, category_id: str, user_id: str) -> bool:
        """Remove uma categoria."""
        query = select(CategoryModel).where(
            and_(
                CategoryModel.id == category_id,
                CategoryModel.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()
        
        if category:
            await self.db.delete(category)
            return True
        return False
    
    async def get_categories_for_prompt(self, user_id: str) -> str:
        """Retorna categorias formatadas para uso em prompts."""
        categories = await self.list_categories(user_id)
        
        expense_cats = [c for c in categories if not c.is_income]
        income_cats = [c for c in categories if c.is_income]
        
        result = "Categorias de Despesas:\n"
        for cat in expense_cats:
            result += f"- {cat.name} (ID: {cat.id})\n"
        
        result += "\nCategorias de Receitas:\n"
        for cat in income_cats:
            result += f"- {cat.name} (ID: {cat.id})\n"
        
        return result
    
    def _to_schema(self, model: CategoryModel) -> Category:
        """Converte modelo para schema."""
        return Category(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            icon=model.icon,
            color=model.color,
            budget_limit=model.budget_limit,
            is_income=model.is_income,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
