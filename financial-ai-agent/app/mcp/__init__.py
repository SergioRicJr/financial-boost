"""
MCP module - Model Context Protocol server implementation.

Permite expor ferramentas via protocolo MCP para integração
com outros sistemas e clientes compatíveis.
"""

from app.mcp.server import MCPServer
from app.mcp.tools import MCPFinancialTools

__all__ = [
    "MCPServer",
    "MCPFinancialTools",
]
