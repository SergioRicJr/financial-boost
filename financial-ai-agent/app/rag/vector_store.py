"""
Vector Store
============

Gerencia o armazenamento e busca de vetores.
Suporta ChromaDB (local) e Qdrant.
"""

import os
from typing import Any, Optional

from loguru import logger

from app.core.config import settings
from app.rag.document_processor import Chunk
from app.services.llm_service import LLMService


class VectorStore:
    """
    Abstração para vector stores.
    
    Suporta:
    - ChromaDB (para desenvolvimento local)
    - Qdrant (para produção)
    """
    
    def __init__(self, collection_name: str = "financial_knowledge"):
        self.collection_name = collection_name
        self.llm = LLMService()
        
        if settings.vector_store_type == "qdrant":
            self._init_qdrant()
        else:
            self._init_chroma()
    
    def _init_chroma(self) -> None:
        """Inicializa ChromaDB."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            # Garantir que o diretório existe
            os.makedirs(settings.vector_store_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=settings.vector_store_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            
            self._store_type = "chroma"
            logger.info(f"ChromaDB initialized at {settings.vector_store_path}")
            
        except ImportError:
            raise ImportError("Install chromadb: pip install chromadb")
    
    def _init_qdrant(self) -> None:
        """Inicializa Qdrant."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
            
            # Criar collection se não existir
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embeddings
                        distance=Distance.COSINE,
                    ),
                )
            
            self._store_type = "qdrant"
            logger.info(f"Qdrant initialized at {settings.qdrant_host}:{settings.qdrant_port}")
            
        except ImportError:
            raise ImportError("Install qdrant-client: pip install qdrant-client")
    
    async def add_chunks(self, chunks: list[Chunk]) -> None:
        """
        Adiciona chunks ao vector store.
        
        Args:
            chunks: Lista de chunks para adicionar
        """
        if not chunks:
            return
        
        # Gerar embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.llm.embed_batch(texts)
        
        if self._store_type == "chroma":
            await self._add_to_chroma(chunks, embeddings)
        else:
            await self._add_to_qdrant(chunks, embeddings)
        
        logger.info(f"Added {len(chunks)} chunks to {self._store_type}")
    
    async def _add_to_chroma(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        """Adiciona ao ChromaDB."""
        self.collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.content for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
        )
    
    async def _add_to_qdrant(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        """Adiciona ao Qdrant."""
        from qdrant_client.models import PointStruct
        
        points = [
            PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    **chunk.metadata,
                },
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
    
    async def search(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Busca chunks similares à query.
        
        Args:
            query: Texto da busca
            top_k: Número de resultados
            filter_metadata: Filtros opcionais
            
        Returns:
            Lista de resultados com score e metadados
        """
        top_k = top_k or settings.rag_top_k
        
        # Gerar embedding da query
        query_embedding = await self.llm.embed(query)
        
        if self._store_type == "chroma":
            return await self._search_chroma(query_embedding, top_k, filter_metadata)
        else:
            return await self._search_qdrant(query_embedding, top_k, filter_metadata)
    
    async def _search_chroma(
        self,
        query_embedding: list[float],
        top_k: int,
        filter_metadata: Optional[dict],
    ) -> list[dict]:
        """Busca no ChromaDB."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )
        
        items = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                items.append({
                    "chunk_id": chunk_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i],  # Converter distância para score
                })
        
        return items
    
    async def _search_qdrant(
        self,
        query_embedding: list[float],
        top_k: int,
        filter_metadata: Optional[dict],
    ) -> list[dict]:
        """Busca no Qdrant."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Construir filtro se necessário
        search_filter = None
        if filter_metadata:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_metadata.items()
            ]
            search_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter,
        )
        
        return [
            {
                "chunk_id": hit.payload.get("chunk_id"),
                "content": hit.payload.get("content"),
                "metadata": {
                    k: v for k, v in hit.payload.items()
                    if k not in ["chunk_id", "content"]
                },
                "score": hit.score,
            }
            for hit in results
        ]
    
    async def delete_collection(self) -> None:
        """Remove a collection."""
        if self._store_type == "chroma":
            self.client.delete_collection(self.collection_name)
        else:
            self.client.delete_collection(self.collection_name)
        
        logger.info(f"Collection {self.collection_name} deleted")
    
    def get_stats(self) -> dict:
        """Retorna estatísticas da collection."""
        if self._store_type == "chroma":
            count = self.collection.count()
            return {"type": "chroma", "count": count}
        else:
            info = self.client.get_collection(self.collection_name)
            return {
                "type": "qdrant",
                "count": info.points_count,
                "vectors_count": info.vectors_count,
            }
