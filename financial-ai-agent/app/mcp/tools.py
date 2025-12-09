"""
MCP Financial Tools
===================

Definição das ferramentas no formato MCP.
"""

from typing import Any


# Definição das ferramentas no formato MCP
MCP_TOOLS_DEFINITION = [
    {
        "name": "create_transaction",
        "description": "Cria uma nova transação financeira (receita ou despesa)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Descrição da transação (ex: 'Almoço no restaurante')"
                },
                "amount": {
                    "type": "number",
                    "description": "Valor em reais (sempre positivo)"
                },
                "transaction_type": {
                    "type": "string",
                    "enum": ["income", "expense"],
                    "description": "Tipo: 'income' para receita ou 'expense' para despesa"
                },
                "category": {
                    "type": "string",
                    "description": "Nome da categoria (opcional)"
                },
                "date": {
                    "type": "string",
                    "description": "Data no formato YYYY-MM-DD (opcional, padrão: hoje)"
                }
            },
            "required": ["description", "amount", "transaction_type"]
        }
    },
    {
        "name": "get_transactions",
        "description": "Lista as transações do usuário com filtros opcionais",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Número máximo de transações (padrão: 10)"
                },
                "start_date": {
                    "type": "string",
                    "description": "Data inicial no formato YYYY-MM-DD"
                },
                "end_date": {
                    "type": "string",
                    "description": "Data final no formato YYYY-MM-DD"
                },
                "category": {
                    "type": "string",
                    "description": "Filtrar por nome da categoria"
                }
            }
        }
    },
    {
        "name": "get_financial_summary",
        "description": "Retorna um resumo financeiro do período especificado",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["week", "month", "quarter", "year"],
                    "description": "Período do resumo"
                }
            }
        }
    },
    {
        "name": "analyze_finances",
        "description": "Executa uma análise financeira detalhada com IA",
        "inputSchema": {
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": ["health", "patterns", "recommendations", "prediction"],
                    "description": "Tipo de análise: health (saúde financeira), patterns (padrões), recommendations (recomendações), prediction (previsões)"
                }
            }
        }
    },
    {
        "name": "set_budget",
        "description": "Define ou atualiza o limite de orçamento de uma categoria",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Nome da categoria"
                },
                "amount": {
                    "type": "number",
                    "description": "Valor limite do orçamento em reais"
                }
            },
            "required": ["category", "amount"]
        }
    },
    {
        "name": "search_transactions",
        "description": "Busca transações por texto na descrição",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Texto para buscar nas descrições"
                },
                "limit": {
                    "type": "integer",
                    "description": "Número máximo de resultados (padrão: 10)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_spending_by_category",
        "description": "Retorna detalhes de gastos de uma categoria específica",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Nome da categoria"
                },
                "period": {
                    "type": "string",
                    "enum": ["week", "month", "year"],
                    "description": "Período da análise"
                }
            },
            "required": ["category"]
        }
    },
    {
        "name": "categorize_transaction",
        "description": "Sugere a melhor categoria para uma transação usando IA",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Descrição da transação"
                },
                "amount": {
                    "type": "number",
                    "description": "Valor da transação"
                }
            },
            "required": ["description", "amount"]
        }
    },
    {
        "name": "ask_financial_question",
        "description": "Faz uma pergunta sobre finanças pessoais usando RAG",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Pergunta sobre finanças pessoais"
                }
            },
            "required": ["question"]
        }
    }
]


class MCPFinancialTools:
    """
    Implementação das ferramentas MCP para finanças.
    
    Cada método corresponde a uma ferramenta definida em MCP_TOOLS_DEFINITION.
    """
    
    def __init__(self, context: dict[str, Any]):
        self.context = context
    
    @staticmethod
    def get_tools_definition() -> list[dict]:
        """Retorna a definição das ferramentas no formato MCP."""
        return MCP_TOOLS_DEFINITION
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Executa uma ferramenta pelo nome.
        
        Args:
            tool_name: Nome da ferramenta
            arguments: Argumentos da ferramenta
            
        Returns:
            Resultado da execução
        """
        handlers = {
            "create_transaction": self._create_transaction,
            "get_transactions": self._get_transactions,
            "get_financial_summary": self._get_financial_summary,
            "analyze_finances": self._analyze_finances,
            "set_budget": self._set_budget,
            "search_transactions": self._search_transactions,
            "get_spending_by_category": self._get_spending_by_category,
            "categorize_transaction": self._categorize_transaction,
            "ask_financial_question": self._ask_financial_question,
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            return {
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(handlers.keys()),
            }
        
        try:
            result = await handler(**arguments)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_transaction(
        self,
        description: str,
        amount: float,
        transaction_type: str,
        category: str = None,
        date: str = None,
    ) -> str:
        """Cria uma transação."""
        # Implementação conectaria ao TransactionService
        return f"Transação '{description}' de R$ {amount:.2f} criada com sucesso"
    
    async def _get_transactions(
        self,
        limit: int = 10,
        start_date: str = None,
        end_date: str = None,
        category: str = None,
    ) -> list[dict]:
        """Lista transações."""
        # Implementação conectaria ao TransactionService
        return [
            {"description": "Salário", "amount": 5000, "type": "income"},
            {"description": "Aluguel", "amount": 1500, "type": "expense"},
        ]
    
    async def _get_financial_summary(self, period: str = "month") -> dict:
        """Retorna resumo financeiro."""
        return {
            "period": period,
            "income": 5000,
            "expenses": 3200,
            "balance": 1800,
            "savings_rate": 36,
        }
    
    async def _analyze_finances(self, analysis_type: str = "health") -> dict:
        """Executa análise financeira."""
        return {
            "type": analysis_type,
            "score": 75,
            "grade": "B",
            "insights": ["Taxa de poupança acima da média"],
        }
    
    async def _set_budget(self, category: str, amount: float) -> str:
        """Define orçamento."""
        return f"Orçamento de R$ {amount:.2f} definido para {category}"
    
    async def _search_transactions(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """Busca transações."""
        return []
    
    async def _get_spending_by_category(
        self,
        category: str,
        period: str = "month",
    ) -> dict:
        """Retorna gastos por categoria."""
        return {
            "category": category,
            "period": period,
            "total": 650,
            "budget": 800,
            "percentage_used": 81,
        }
    
    async def _categorize_transaction(
        self,
        description: str,
        amount: float,
    ) -> dict:
        """Sugere categoria."""
        return {
            "suggested_category": "Alimentação",
            "confidence": 0.95,
        }
    
    async def _ask_financial_question(self, question: str) -> str:
        """Responde pergunta financeira usando RAG."""
        # Conectaria ao FinancialRetriever
        return "Resposta baseada na base de conhecimento financeiro."
