"""
Analysis Service
================

Serviço para análises financeiras usando IA.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.analysis import (
    FinancialSummary,
    SpendingPattern,
    BudgetRecommendation,
    FinancialHealth,
    PredictionResult,
)
from app.services.transaction_service import TransactionService
from app.services.category_service import CategoryService
from app.services.llm_service import LLMService


class AnalysisService:
    """Serviço de análises financeiras."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.transaction_service = TransactionService(db)
        self.category_service = CategoryService(db)
        self.llm = LLMService()
    
    async def generate_financial_summary(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Gera um resumo financeiro completo com insights da IA."""
        
        # Buscar dados básicos
        summary = await self.transaction_service.get_summary(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        transactions = await self.transaction_service.get_transactions_for_analysis(
            user_id=user_id,
            days=90,
        )
        
        # Gerar análise com IA
        analysis_prompt = self._build_analysis_prompt(summary, transactions)
        
        response = await self.llm.complete(
            messages=[
                {
                    "role": "system",
                    "content": """Você é um analista financeiro especializado em finanças pessoais.
                    Analise os dados fornecidos e gere insights úteis e práticos.
                    Responda em português brasileiro.
                    Seja específico nas recomendações e use números quando possível.""",
                },
                {"role": "user", "content": analysis_prompt},
            ],
            temperature=0.7,
        )
        
        # Extrair insights estruturados
        insights = await self._extract_insights(response["content"])
        
        return {
            **summary,
            "ai_analysis": response["content"],
            "insights": insights,
        }
    
    async def identify_spending_patterns(
        self,
        user_id: str,
    ) -> list[SpendingPattern]:
        """Identifica padrões de gastos usando IA."""
        
        transactions = await self.transaction_service.get_transactions_for_analysis(
            user_id=user_id,
            days=180,
        )
        
        if len(transactions) < 10:
            return []
        
        prompt = f"""Analise as seguintes transações financeiras e identifique padrões de gastos:

{json.dumps(transactions[:100], ensure_ascii=False, indent=2)}

Identifique:
1. Gastos recorrentes (assinaturas, contas mensais)
2. Padrões sazonais
3. Gastos incomuns ou fora do padrão
4. Tendências de aumento ou diminuição

Para cada padrão, forneça:
- Tipo do padrão
- Descrição clara
- Categoria relacionada
- Valor médio
- Frequência (se aplicável)
- Nível de confiança (0-1)
- Recomendação

Responda em formato JSON com uma lista de padrões."""

        response = await self.llm.complete(
            messages=[
                {
                    "role": "system",
                    "content": "Você é um analista financeiro. Responda apenas com JSON válido.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        
        try:
            # Tentar extrair JSON da resposta
            content = response["content"]
            # Encontrar o JSON na resposta
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                patterns_data = json.loads(content[start:end])
                return [
                    SpendingPattern(
                        pattern_type=p.get("type", "unknown"),
                        description=p.get("description", ""),
                        category=p.get("category"),
                        average_amount=Decimal(str(p.get("average_amount", 0))),
                        frequency=p.get("frequency"),
                        confidence=float(p.get("confidence", 0.5)),
                        recommendation=p.get("recommendation"),
                    )
                    for p in patterns_data
                ]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Erro ao parsear padrões: {e}")
        
        return []
    
    async def get_budget_recommendations(
        self,
        user_id: str,
    ) -> list[BudgetRecommendation]:
        """Gera recomendações de orçamento personalizadas."""
        
        summary = await self.transaction_service.get_summary(user_id=user_id)
        categories = await self.category_service.list_categories(user_id=user_id)
        
        prompt = f"""Com base no seguinte resumo financeiro:

Receita total: R$ {summary['total_income']:.2f}
Despesas totais: R$ {summary['total_expenses']:.2f}
Taxa de poupança: {summary['savings_rate']:.1f}%

Gastos por categoria:
{json.dumps(summary['expenses_by_category'], ensure_ascii=False, indent=2)}

Categorias disponíveis:
{', '.join(c.name for c in categories if not c.is_income)}

Gere recomendações de orçamento para cada categoria, considerando:
1. A regra 50/30/20 (necessidades/desejos/poupança)
2. Oportunidades de economia
3. Priorização baseada em impacto

Para cada recomendação, forneça:
- Categoria
- Gasto atual
- Orçamento recomendado
- Economia potencial
- Prioridade (high/medium/low)
- Justificativa
- Ações práticas

Responda em formato JSON."""

        response = await self.llm.complete(
            messages=[
                {
                    "role": "system",
                    "content": "Você é um planejador financeiro. Responda apenas com JSON válido.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        
        try:
            content = response["content"]
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                recommendations_data = json.loads(content[start:end])
                return [
                    BudgetRecommendation(
                        category=r.get("category", ""),
                        current_spending=Decimal(str(r.get("current_spending", 0))),
                        recommended_budget=Decimal(str(r.get("recommended_budget", 0))),
                        potential_savings=Decimal(str(r.get("potential_savings", 0))),
                        priority=r.get("priority", "medium"),
                        rationale=r.get("rationale", ""),
                        action_items=r.get("action_items", []),
                    )
                    for r in recommendations_data
                ]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Erro ao parsear recomendações: {e}")
        
        return []
    
    async def calculate_financial_health(
        self,
        user_id: str,
    ) -> FinancialHealth:
        """Calcula o score de saúde financeira."""
        
        summary = await self.transaction_service.get_summary(user_id=user_id)
        
        # Cálculos básicos
        savings_rate = summary["savings_rate"]
        
        # Score simplificado baseado na taxa de poupança
        if savings_rate >= 20:
            score = min(100, 70 + savings_rate)
            grade = "A" if score >= 90 else "B"
        elif savings_rate >= 10:
            score = 50 + savings_rate * 2
            grade = "B" if score >= 70 else "C"
        elif savings_rate >= 0:
            score = 30 + savings_rate * 2
            grade = "C" if score >= 50 else "D"
        else:
            score = max(0, 30 + savings_rate)
            grade = "F"
        
        # Gerar análise com IA
        prompt = f"""Analise a saúde financeira com base nos dados:

Receita: R$ {summary['total_income']:.2f}
Despesas: R$ {summary['total_expenses']:.2f}
Taxa de poupança: {savings_rate:.1f}%
Score calculado: {score}/100

Liste:
1. 3 pontos fortes
2. 3 pontos a melhorar
3. 5 recomendações práticas

Responda em JSON com as chaves: strengths, weaknesses, recommendations (arrays de strings)."""

        response = await self.llm.complete(
            messages=[
                {
                    "role": "system",
                    "content": "Você é um consultor financeiro. Responda apenas com JSON válido.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )
        
        try:
            content = response["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                analysis = json.loads(content[start:end])
                
                return FinancialHealth(
                    score=int(score),
                    grade=grade,
                    savings_rate=savings_rate,
                    debt_to_income_ratio=None,
                    emergency_fund_months=0,
                    budget_adherence=0,
                    strengths=analysis.get("strengths", []),
                    weaknesses=analysis.get("weaknesses", []),
                    recommendations=analysis.get("recommendations", []),
                )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Erro ao parsear saúde financeira: {e}")
        
        return FinancialHealth(
            score=int(score),
            grade=grade,
            savings_rate=savings_rate,
            debt_to_income_ratio=None,
            emergency_fund_months=0,
            budget_adherence=0,
            strengths=["Dados insuficientes para análise detalhada"],
            weaknesses=["Dados insuficientes para análise detalhada"],
            recommendations=["Registre mais transações para uma análise completa"],
        )
    
    async def categorize_transaction(
        self,
        user_id: str,
        description: str,
        amount: float,
    ) -> dict:
        """Sugere categoria para uma transação usando IA."""
        
        categories = await self.category_service.list_categories(user_id=user_id)
        categories_list = [
            {"id": c.id, "name": c.name, "is_income": c.is_income}
            for c in categories
        ]
        
        prompt = f"""Categorize a seguinte transação:

Descrição: {description}
Valor: R$ {amount:.2f}

Categorias disponíveis:
{json.dumps(categories_list, ensure_ascii=False, indent=2)}

Responda em JSON com:
- category_id: ID da categoria mais adequada
- category_name: Nome da categoria
- confidence: Nível de confiança (0-1)
- reasoning: Explicação breve"""

        response = await self.llm.complete(
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente de categorização financeira. Responda apenas com JSON válido.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        
        try:
            content = response["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Erro ao categorizar: {e}")
        
        return {
            "category_id": None,
            "category_name": "Outros",
            "confidence": 0.5,
            "reasoning": "Não foi possível categorizar automaticamente",
        }
    
    def _build_analysis_prompt(
        self,
        summary: dict,
        transactions: list[dict],
    ) -> str:
        """Constrói o prompt para análise financeira."""
        
        return f"""Analise os dados financeiros abaixo e forneça insights detalhados:

## Resumo do Período ({summary['period']['start']} a {summary['period']['end']}):
- Receita total: R$ {summary['total_income']:.2f}
- Despesas totais: R$ {summary['total_expenses']:.2f}
- Saldo líquido: R$ {summary['net_balance']:.2f}
- Taxa de poupança: {summary['savings_rate']:.1f}%

## Gastos por Categoria:
{json.dumps(summary['expenses_by_category'], ensure_ascii=False, indent=2)}

## Últimas Transações (amostra):
{json.dumps(transactions[:20], ensure_ascii=False, indent=2)}

Por favor, forneça:
1. Uma análise geral da situação financeira
2. Os 3 principais pontos de atenção
3. Oportunidades de economia identificadas
4. Recomendações práticas e específicas
5. Previsão para o próximo mês

Use linguagem clara e acessível, com valores em reais."""
    
    async def _extract_insights(self, analysis_text: str) -> list[str]:
        """Extrai insights principais da análise."""
        
        prompt = f"""Do texto de análise abaixo, extraia os 5 insights mais importantes como uma lista JSON de strings curtas (máximo 100 caracteres cada):

{analysis_text}

Responda apenas com o array JSON."""

        response = await self.llm.complete(
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        
        try:
            content = response["content"]
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except (json.JSONDecodeError, KeyError):
            pass
        
        return ["Análise completa disponível no resumo detalhado"]
