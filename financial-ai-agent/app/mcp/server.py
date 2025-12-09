"""
MCP Server
==========

Servidor MCP (Model Context Protocol) para expor ferramentas financeiras.
"""

import json
from typing import Any, Optional

from loguru import logger

from app.mcp.tools import MCPFinancialTools, MCP_TOOLS_DEFINITION


class MCPServer:
    """
    Servidor MCP para ferramentas financeiras.
    
    Implementa o protocolo MCP para permitir que clientes
    externos utilizem as ferramentas financeiras.
    
    O MCP (Model Context Protocol) é um protocolo aberto que
    padroniza como aplicações fornecem contexto para LLMs.
    """
    
    def __init__(self, context: Optional[dict] = None):
        self.context = context or {}
        self.tools = MCPFinancialTools(self.context)
        self._initialized = False
    
    async def initialize(self) -> dict:
        """
        Inicializa o servidor MCP.
        
        Returns:
            Informações do servidor
        """
        self._initialized = True
        
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "financial-ai-agent",
                "version": "1.0.0",
            },
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
            },
        }
    
    async def list_tools(self) -> dict:
        """
        Lista ferramentas disponíveis.
        
        Returns:
            Lista de ferramentas no formato MCP
        """
        return {
            "tools": MCP_TOOLS_DEFINITION,
        }
    
    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> dict:
        """
        Executa uma ferramenta.
        
        Args:
            name: Nome da ferramenta
            arguments: Argumentos da ferramenta
            
        Returns:
            Resultado da execução
        """
        logger.info(f"MCP tool call: {name} with args: {arguments}")
        
        result = await self.tools.execute_tool(name, arguments)
        
        if result.get("success"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result["result"], ensure_ascii=False, indent=2)
                        if isinstance(result["result"], (dict, list))
                        else str(result["result"]),
                    }
                ],
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Erro: {result.get('error', 'Unknown error')}",
                    }
                ],
                "isError": True,
            }
    
    async def handle_message(self, message: dict) -> dict:
        """
        Processa mensagem MCP.
        
        Args:
            message: Mensagem no formato JSON-RPC
            
        Returns:
            Resposta no formato JSON-RPC
        """
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        try:
            if method == "initialize":
                result = await self.initialize()
            elif method == "tools/list":
                result = await self.list_tools()
            elif method == "tools/call":
                result = await self.call_tool(
                    params.get("name"),
                    params.get("arguments", {}),
                )
            elif method == "resources/list":
                result = {"resources": []}
            elif method == "prompts/list":
                result = {"prompts": []}
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result,
            }
            
        except Exception as e:
            logger.error(f"MCP error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": str(e),
                },
            }
    
    def get_tools_for_llm(self) -> list[dict]:
        """
        Retorna ferramentas no formato OpenAI/Anthropic.
        
        Útil para usar com LLMs que não suportam MCP diretamente.
        """
        openai_tools = []
        
        for tool in MCP_TOOLS_DEFINITION:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"],
                },
            })
        
        return openai_tools
