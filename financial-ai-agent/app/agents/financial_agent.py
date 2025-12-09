"""
Financial Agent
===============

Agente principal usando LangGraph para orquestração.
"""

import json
import uuid
from datetime import datetime
from typing import Annotated, Any, AsyncIterator, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger

from app.agents.prompts import FINANCIAL_AGENT_SYSTEM_PROMPT
from app.agents.tools import FinancialTools
from app.core.config import settings
from app.services.llm_service import LLMService


class AgentState(TypedDict):
    """Estado do agente durante a execução."""
    messages: Annotated[list, add_messages]
    user_id: str
    conversation_id: str
    context: dict[str, Any]
    tool_calls_count: int


class FinancialAgent:
    """
    Agente financeiro usando LangGraph.
    
    Implementa um grafo de estados para processar mensagens do usuário,
    decidir quando usar ferramentas, e gerar respostas.
    """
    
    def __init__(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[dict] = None,
    ):
        self.user_id = user_id
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.context = context or {}
        
        self.llm = LLMService()
        self.tools = FinancialTools({"user_id": user_id, **self.context})
        
        # Construir o grafo
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo de estados do agente."""
        
        # Criar o grafo
        workflow = StateGraph(AgentState)
        
        # Adicionar nós
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tools_node)
        
        # Definir o ponto de entrada
        workflow.set_entry_point("agent")
        
        # Adicionar edges condicionais
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END,
            }
        )
        
        # Tools sempre volta para o agent
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    async def _agent_node(self, state: AgentState) -> dict:
        """Nó principal do agente que processa mensagens e decide ações."""
        
        messages = state["messages"]
        
        # Preparar mensagens no formato do LLM
        formatted_messages = self._format_messages(messages)
        
        # Preparar tools no formato OpenAI
        tools_schema = self._get_tools_schema()
        
        # Chamar o LLM
        response = await self.llm.complete(
            messages=formatted_messages,
            tools=tools_schema if tools_schema else None,
            tool_choice="auto" if tools_schema else None,
        )
        
        # Processar resposta
        if response.get("tool_calls"):
            # LLM quer usar ferramentas
            tool_calls = response["tool_calls"]
            
            ai_message = AIMessage(
                content=response.get("content") or "",
                tool_calls=[
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "args": json.loads(tc.function.arguments),
                    }
                    for tc in tool_calls
                ]
            )
            
            return {
                "messages": [ai_message],
                "tool_calls_count": state.get("tool_calls_count", 0) + len(tool_calls),
            }
        else:
            # Resposta final
            return {
                "messages": [AIMessage(content=response["content"])],
            }
    
    async def _tools_node(self, state: AgentState) -> dict:
        """Nó que executa as ferramentas solicitadas."""
        
        messages = state["messages"]
        last_message = messages[-1]
        
        tool_messages = []
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                # Encontrar e executar a tool
                result = await self._execute_tool(tool_name, tool_args)
                
                tool_messages.append(
                    ToolMessage(
                        content=result,
                        tool_call_id=tool_id,
                    )
                )
        
        return {"messages": tool_messages}
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """Decide se deve continuar para tools ou finalizar."""
        
        messages = state["messages"]
        last_message = messages[-1]
        
        # Limite de chamadas de tools para evitar loops
        if state.get("tool_calls_count", 0) > 10:
            logger.warning("Tool calls limit reached")
            return "end"
        
        # Se a última mensagem tem tool_calls, continua
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        
        return "end"
    
    def _format_messages(self, messages: list) -> list[dict]:
        """Formata mensagens para o formato do LLM."""
        
        formatted = [
            {"role": "system", "content": FINANCIAL_AGENT_SYSTEM_PROMPT}
        ]
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                msg_dict = {"role": "assistant", "content": msg.content or ""}
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["args"]),
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                formatted.append(msg_dict)
            elif isinstance(msg, ToolMessage):
                formatted.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id,
                })
            elif isinstance(msg, SystemMessage):
                formatted.append({"role": "system", "content": msg.content})
        
        return formatted
    
    def _get_tools_schema(self) -> list[dict]:
        """Retorna o schema das ferramentas no formato OpenAI."""
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_transaction",
                    "description": "Cria uma nova transação financeira (receita ou despesa)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Descrição da transação"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Valor em reais"
                            },
                            "transaction_type": {
                                "type": "string",
                                "enum": ["income", "expense"],
                                "description": "Tipo: income (receita) ou expense (despesa)"
                            },
                            "category": {
                                "type": "string",
                                "description": "Nome da categoria (opcional)"
                            },
                            "date": {
                                "type": "string",
                                "description": "Data no formato YYYY-MM-DD (opcional)"
                            }
                        },
                        "required": ["description", "amount", "transaction_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_transactions",
                    "description": "Lista transações do usuário com filtros opcionais",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de resultados"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Data inicial (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "Data final (YYYY-MM-DD)"
                            },
                            "category": {
                                "type": "string",
                                "description": "Filtrar por categoria"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_financial_summary",
                    "description": "Retorna resumo financeiro do período",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period": {
                                "type": "string",
                                "enum": ["week", "month", "quarter", "year"],
                                "description": "Período do resumo"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_categories",
                    "description": "Lista categorias disponíveis",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "include_budgets": {
                                "type": "boolean",
                                "description": "Incluir limites de orçamento"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_finances",
                    "description": "Executa análise financeira detalhada",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "enum": ["health", "patterns", "recommendations", "prediction"],
                                "description": "Tipo de análise"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "categorize_transaction",
                    "description": "Sugere categoria para uma transação",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_budget",
                    "description": "Define limite de orçamento para categoria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Nome da categoria"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Valor limite mensal"
                            }
                        },
                        "required": ["category", "amount"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_spending_by_category",
                    "description": "Detalha gastos de uma categoria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Nome da categoria"
                            },
                            "period": {
                                "type": "string",
                                "enum": ["week", "month", "year"],
                                "description": "Período"
                            }
                        },
                        "required": ["category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_transactions",
                    "description": "Busca transações por texto",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Texto para buscar"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Máximo de resultados"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        return tools
    
    async def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Executa uma ferramenta pelo nome."""
        
        tools_map = {
            "create_transaction": self.tools.create_transaction,
            "get_transactions": self.tools.get_transactions,
            "get_financial_summary": self.tools.get_financial_summary,
            "get_categories": self.tools.get_categories,
            "analyze_finances": self.tools.analyze_finances,
            "categorize_transaction": self.tools.categorize_transaction,
            "set_budget": self.tools.set_budget,
            "get_spending_by_category": self.tools.get_spending_by_category,
            "search_transactions": self.tools.search_transactions,
        }
        
        tool_func = tools_map.get(tool_name)
        if not tool_func:
            return f"Ferramenta '{tool_name}' não encontrada."
        
        try:
            # As tools são assíncronas
            result = await tool_func(**args)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Erro ao executar ferramenta: {str(e)}"
    
    async def chat(self, message: str) -> str:
        """
        Processa uma mensagem do usuário e retorna a resposta.
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Resposta do agente
        """
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "context": self.context,
            "tool_calls_count": 0,
        }
        
        # Executar o grafo
        result = await self.graph.ainvoke(initial_state)
        
        # Extrair a última mensagem do assistente
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
        
        return "Desculpe, não consegui processar sua mensagem."
    
    async def chat_stream(self, message: str) -> AsyncIterator[str]:
        """
        Processa uma mensagem com streaming da resposta.
        
        Args:
            message: Mensagem do usuário
            
        Yields:
            Chunks da resposta
        """
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "context": self.context,
            "tool_calls_count": 0,
        }
        
        # Para streaming, usamos astream_events
        async for event in self.graph.astream_events(initial_state, version="v1"):
            kind = event["event"]
            
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
            
            elif kind == "on_tool_start":
                tool_name = event["name"]
                yield f"\n🔧 Usando ferramenta: {tool_name}...\n"
            
            elif kind == "on_tool_end":
                yield "\n"
