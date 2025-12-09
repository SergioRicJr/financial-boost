"""
Financial Tools
===============

Ferramentas disponíveis para os agentes de IA.
Seguem o padrão de tools do LangChain/LangGraph.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from langchain_core.tools import tool
from loguru import logger
from pydantic import BaseModel, Field


class TransactionInput(BaseModel):
    """Input para criar transação."""
    description: str = Field(description="Descrição da transação")
    amount: float = Field(description="Valor da transação")
    type: str = Field(description="Tipo: 'income' ou 'expense'")
    category: Optional[str] = Field(default=None, description="Nome da categoria")
    date: Optional[str] = Field(default=None, description="Data no formato YYYY-MM-DD")


class QueryInput(BaseModel):
    """Input para consultas."""
    query_type: str = Field(description="Tipo de consulta: 'summary', 'transactions', 'categories'")
    start_date: Optional[str] = Field(default=None, description="Data inicial YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="Data final YYYY-MM-DD")
    category: Optional[str] = Field(default=None, description="Filtrar por categoria")
    limit: int = Field(default=10, description="Número máximo de resultados")


class AnalysisInput(BaseModel):
    """Input para análises."""
    analysis_type: str = Field(
        description="Tipo: 'health', 'patterns', 'recommendations', 'prediction'"
    )
    period_days: int = Field(default=30, description="Período em dias para análise")


class FinancialTools:
    """
    Classe que agrupa as ferramentas financeiras.
    
    Cada método é uma tool que pode ser chamada pelos agentes.
    """
    
    def __init__(self, context: dict[str, Any]):
        """
        Inicializa as tools com contexto.
        
        Args:
            context: Dicionário com dependências (db, user_id, services)
        """
        self.context = context
    
    def get_tools(self) -> list:
        """Retorna lista de tools disponíveis."""
        return [
            self.create_transaction,
            self.get_transactions,
            self.get_financial_summary,
            self.get_categories,
            self.analyze_finances,
            self.categorize_transaction,
            self.set_budget,
            self.get_spending_by_category,
            self.search_transactions,
        ]
    
    @tool
    async def create_transaction(
        self,
        description: str,
        amount: float,
        transaction_type: str,
        category: Optional[str] = None,
        date: Optional[str] = None,
    ) -> str:
        """
        Cria uma nova transação financeira.
        
        Args:
            description: Descrição da transação (ex: "Almoço no restaurante")
            amount: Valor em reais (sempre positivo)
            transaction_type: Tipo da transação - "income" para receita ou "expense" para despesa
            category: Nome da categoria (opcional)
            date: Data da transação no formato YYYY-MM-DD (opcional, padrão: hoje)
        
        Returns:
            Confirmação da transação criada com detalhes
        """
        # Esta é uma implementação placeholder
        # Na prática, seria conectada ao TransactionService
        logger.info(f"Creating transaction: {description} - R$ {amount}")
        
        return f"""✅ Transação registrada com sucesso!

📝 Detalhes:
- Descrição: {description}
- Valor: R$ {amount:.2f}
- Tipo: {"Receita" if transaction_type == "income" else "Despesa"}
- Categoria: {category or "Não categorizado"}
- Data: {date or datetime.now().strftime("%Y-%m-%d")}
"""
    
    @tool
    async def get_transactions(
        self,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
    ) -> str:
        """
        Lista as transações recentes do usuário.
        
        Args:
            limit: Número máximo de transações (padrão: 10)
            start_date: Data inicial no formato YYYY-MM-DD
            end_date: Data final no formato YYYY-MM-DD
            category: Filtrar por nome da categoria
        
        Returns:
            Lista formatada de transações
        """
        # Implementação placeholder
        logger.info(f"Fetching transactions - limit: {limit}")
        
        # Simular algumas transações
        sample_transactions = [
            {"desc": "Salário", "amount": 5000, "type": "income", "cat": "Salário"},
            {"desc": "Aluguel", "amount": 1500, "type": "expense", "cat": "Moradia"},
            {"desc": "Supermercado", "amount": 450, "type": "expense", "cat": "Alimentação"},
            {"desc": "Uber", "amount": 85, "type": "expense", "cat": "Transporte"},
            {"desc": "Netflix", "amount": 55, "type": "expense", "cat": "Lazer"},
        ]
        
        result = "📋 **Últimas Transações:**\n\n"
        for i, t in enumerate(sample_transactions[:limit], 1):
            emoji = "💰" if t["type"] == "income" else "💸"
            result += f"{i}. {emoji} {t['desc']} - R$ {t['amount']:.2f} ({t['cat']})\n"
        
        return result
    
    @tool
    async def get_financial_summary(
        self,
        period: str = "month",
    ) -> str:
        """
        Retorna um resumo financeiro do período.
        
        Args:
            period: Período do resumo - "week", "month", "quarter" ou "year"
        
        Returns:
            Resumo financeiro formatado com totais e métricas
        """
        logger.info(f"Getting financial summary for period: {period}")
        
        # Dados de exemplo
        summary = {
            "income": 5000,
            "expenses": 3200,
            "balance": 1800,
            "savings_rate": 36,
        }
        
        return f"""📊 **Resumo Financeiro - {period.capitalize()}**

💰 **Receitas:** R$ {summary['income']:.2f}
💸 **Despesas:** R$ {summary['expenses']:.2f}
📈 **Saldo:** R$ {summary['balance']:.2f}
🎯 **Taxa de Poupança:** {summary['savings_rate']}%

**Top Categorias de Gastos:**
1. 🏠 Moradia: R$ 1.500,00 (47%)
2. 🍽️ Alimentação: R$ 650,00 (20%)
3. 🚗 Transporte: R$ 400,00 (13%)
"""
    
    @tool
    async def get_categories(self, include_budgets: bool = True) -> str:
        """
        Lista todas as categorias do usuário.
        
        Args:
            include_budgets: Se deve incluir limites de orçamento
        
        Returns:
            Lista de categorias com seus detalhes
        """
        logger.info("Fetching categories")
        
        categories = [
            {"name": "Alimentação", "icon": "🍽️", "budget": 800},
            {"name": "Transporte", "icon": "🚗", "budget": 500},
            {"name": "Moradia", "icon": "🏠", "budget": 1500},
            {"name": "Lazer", "icon": "🎮", "budget": 300},
            {"name": "Saúde", "icon": "🏥", "budget": 200},
            {"name": "Salário", "icon": "💰", "budget": None},
        ]
        
        result = "📁 **Categorias Disponíveis:**\n\n"
        
        for cat in categories:
            budget_str = f" (Orçamento: R$ {cat['budget']:.2f})" if cat['budget'] and include_budgets else ""
            result += f"{cat['icon']} {cat['name']}{budget_str}\n"
        
        return result
    
    @tool
    async def analyze_finances(
        self,
        analysis_type: str = "health",
    ) -> str:
        """
        Executa uma análise financeira detalhada.
        
        Args:
            analysis_type: Tipo de análise:
                - "health": Score de saúde financeira
                - "patterns": Identificação de padrões de gastos
                - "recommendations": Recomendações de orçamento
                - "prediction": Previsão de gastos futuros
        
        Returns:
            Análise detalhada com insights e recomendações
        """
        logger.info(f"Running analysis: {analysis_type}")
        
        if analysis_type == "health":
            return """🏥 **Análise de Saúde Financeira**

📊 **Score:** 75/100 (Bom)
📈 **Nota:** B

**Pontos Fortes:**
✅ Taxa de poupança acima de 30%
✅ Despesas controladas na maioria das categorias
✅ Sem gastos recorrentes excessivos

**Pontos de Atenção:**
⚠️ Gastos com alimentação acima da média
⚠️ Sem reserva de emergência identificada
⚠️ Considere diversificar investimentos

**Recomendações:**
1. 💡 Monte uma reserva de emergência de 6 meses
2. 💡 Reduza gastos com delivery em 20%
3. 💡 Automatize transferências para investimentos
"""
        
        elif analysis_type == "patterns":
            return """🔍 **Padrões de Gastos Identificados**

**Gastos Recorrentes:**
📅 Netflix - R$ 55,90/mês
📅 Spotify - R$ 21,90/mês
📅 Academia - R$ 99,90/mês
📅 iFood - ~R$ 200,00/mês (variável)

**Padrões Sazonais:**
📈 Gastos aumentam 30% em dezembro
📉 Economia maior em janeiro/fevereiro

**Gastos Incomuns Detectados:**
⚠️ Compra de R$ 450 em "Eletrônicos" - fora do padrão usual

**Tendência:**
📊 Seus gastos têm se mantido estáveis nos últimos 3 meses
"""
        
        elif analysis_type == "recommendations":
            return """💡 **Recomendações de Orçamento**

Baseado no seu perfil, sugerimos:

**Regra 50/30/20 Adaptada:**
- 50% Necessidades: R$ 2.500 ✅ (você gasta: R$ 2.300)
- 30% Desejos: R$ 1.500 ⚠️ (você gasta: R$ 1.700)
- 20% Poupança: R$ 1.000 ✅ (você poupa: R$ 1.000)

**Ajustes Sugeridos:**
| Categoria | Atual | Sugerido | Economia |
|-----------|-------|----------|----------|
| Alimentação | R$ 800 | R$ 650 | R$ 150 |
| Transporte | R$ 400 | R$ 350 | R$ 50 |
| Lazer | R$ 500 | R$ 400 | R$ 100 |

**Potencial de Economia:** R$ 300/mês
"""
        
        else:
            return """🔮 **Previsão Financeira**

**Próximo Mês:**
- Receita esperada: R$ 5.000
- Despesas previstas: R$ 3.400
- Saldo projetado: R$ 1.600

**Alertas:**
⚠️ Vencimento do IPVA em 15 dias (~R$ 800)
⚠️ Renovação Netflix próxima semana

**Projeção Trimestral:**
Se mantiver o padrão atual:
- Economia acumulada: R$ 4.800
- Reserva de emergência: 1.5 meses de despesas
"""
    
    @tool
    async def categorize_transaction(
        self,
        description: str,
        amount: float,
    ) -> str:
        """
        Sugere a melhor categoria para uma transação.
        
        Args:
            description: Descrição da transação
            amount: Valor da transação
        
        Returns:
            Categoria sugerida com nível de confiança
        """
        logger.info(f"Categorizing: {description}")
        
        # Lógica simplificada de categorização
        description_lower = description.lower()
        
        categories_map = {
            "alimentação": ["restaurante", "almoço", "jantar", "café", "supermercado", "ifood", "delivery"],
            "transporte": ["uber", "99", "gasolina", "combustível", "estacionamento", "ônibus", "metrô"],
            "moradia": ["aluguel", "condomínio", "luz", "água", "gás", "internet"],
            "lazer": ["netflix", "spotify", "cinema", "show", "viagem", "bar"],
            "saúde": ["farmácia", "médico", "hospital", "plano de saúde", "academia"],
        }
        
        for category, keywords in categories_map.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return f"""🏷️ **Sugestão de Categoria**

Transação: "{description}"
Valor: R$ {amount:.2f}

**Categoria Sugerida:** {category.capitalize()}
**Confiança:** 95%

💡 Dica: Você pode confirmar ou escolher outra categoria ao registrar.
"""
        
        return f"""🏷️ **Sugestão de Categoria**

Transação: "{description}"
Valor: R$ {amount:.2f}

**Categoria Sugerida:** Outros
**Confiança:** 60%

❓ Não encontrei uma categoria específica. Por favor, indique a categoria correta.
"""
    
    @tool
    async def set_budget(
        self,
        category: str,
        amount: float,
    ) -> str:
        """
        Define ou atualiza o orçamento de uma categoria.
        
        Args:
            category: Nome da categoria
            amount: Valor limite do orçamento em reais
        
        Returns:
            Confirmação da atualização do orçamento
        """
        logger.info(f"Setting budget for {category}: R$ {amount}")
        
        return f"""✅ **Orçamento Atualizado**

📁 Categoria: {category}
💰 Novo limite: R$ {amount:.2f}/mês

**Status Atual:**
- Gasto no mês: R$ 450,00
- Disponível: R$ {amount - 450:.2f}
- Utilização: {(450/amount)*100:.1f}%

🔔 Você receberá alertas quando atingir 80% do orçamento.
"""
    
    @tool
    async def get_spending_by_category(
        self,
        category: str,
        period: str = "month",
    ) -> str:
        """
        Retorna detalhes de gastos de uma categoria específica.
        
        Args:
            category: Nome da categoria
            period: Período - "week", "month" ou "year"
        
        Returns:
            Detalhamento dos gastos na categoria
        """
        logger.info(f"Getting spending for {category} in {period}")
        
        return f"""📊 **Gastos em {category.capitalize()} - {period.capitalize()}**

💰 **Total:** R$ 650,00
📈 **Média diária:** R$ 21,67
🔄 **vs. mês anterior:** +8%

**Detalhamento:**
1. Supermercado Extra - R$ 280,00 (43%)
2. iFood - R$ 200,00 (31%)
3. Restaurantes - R$ 120,00 (18%)
4. Padaria - R$ 50,00 (8%)

**Orçamento:**
- Limite: R$ 800,00
- Utilizado: R$ 650,00 (81%)
- Disponível: R$ 150,00

⚠️ Você está próximo do limite. Considere reduzir gastos com delivery.
"""
    
    @tool
    async def search_transactions(
        self,
        query: str,
        limit: int = 10,
    ) -> str:
        """
        Busca transações por texto na descrição.
        
        Args:
            query: Texto para buscar
            limit: Número máximo de resultados
        
        Returns:
            Lista de transações encontradas
        """
        logger.info(f"Searching transactions: {query}")
        
        return f"""🔍 **Resultados para "{query}"**

Encontradas 3 transações:

1. 💸 **iFood - {query}** - R$ 45,00
   📅 15/12/2024 | 🏷️ Alimentação
   
2. 💸 **Uber para {query}** - R$ 28,00
   📅 10/12/2024 | 🏷️ Transporte
   
3. 💸 **Compra {query}** - R$ 150,00
   📅 05/12/2024 | 🏷️ Compras

💡 Dica: Use filtros de data para refinar a busca.
"""
