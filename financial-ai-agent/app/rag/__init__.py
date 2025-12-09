"""
RAG module - Retrieval Augmented Generation pipeline.

Permite ao agente acessar conhecimento de documentos
para fornecer respostas mais precisas e contextualizadas.
"""

from app.rag.document_processor import DocumentProcessor
from app.rag.vector_store import VectorStore
from app.rag.retriever import FinancialRetriever

__all__ = [
    "DocumentProcessor",
    "VectorStore",
    "FinancialRetriever",
]
