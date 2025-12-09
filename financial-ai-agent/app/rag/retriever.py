"""
Financial Retriever
===================

Retriever especializado para contexto financeiro.
Combina RAG com conhecimento do domínio financeiro.
"""

from typing import Any, Optional

from loguru import logger

from app.rag.vector_store import VectorStore
from app.rag.document_processor import DocumentProcessor
from app.services.llm_service import LLMService
from app.core.config import settings


# Conhecimento base sobre finanças pessoais
FINANCIAL_KNOWLEDGE_BASE = """
# Guia de Finanças Pessoais

## Regra 50/30/20
A regra 50/30/20 é uma diretriz popular para orçamento:
- 50% da renda para necessidades (moradia, alimentação, transporte, saúde)
- 30% para desejos (lazer, entretenimento, compras não essenciais)
- 20% para poupança e pagamento de dívidas

## Reserva de Emergência
- Ideal: 6 a 12 meses de despesas mensais
- Deve estar em investimento de alta liquidez
- Não deve ser usado para gastos não emergenciais

## Categorias de Gastos
### Necessidades (essenciais)
- Moradia: aluguel, financiamento, condomínio
- Alimentação: supermercado, feira
- Transporte: combustível, transporte público
- Saúde: plano de saúde, medicamentos
- Educação: escola, faculdade

### Desejos (não essenciais)
- Lazer: streaming, restaurantes, viagens
- Compras: roupas, eletrônicos
- Assinaturas: academia, apps

## Indicadores Financeiros
### Taxa de Poupança
- Excelente: > 30%
- Bom: 20-30%
- Regular: 10-20%
- Preocupante: < 10%

### Score de Saúde Financeira
- A (90-100): Excelente gestão financeira
- B (70-89): Boa situação, pequenos ajustes
- C (50-69): Atenção necessária
- D (30-49): Situação preocupante
- F (0-29): Ação urgente necessária

## Dicas de Economia
1. Evite compras por impulso - espere 24h antes de comprar
2. Compare preços antes de grandes compras
3. Reduza assinaturas não utilizadas
4. Prepare refeições em casa
5. Use transporte público quando possível
6. Negocie descontos em serviços recorrentes

## Investimentos para Iniciantes
- Tesouro Direto: baixo risco, ideal para reserva
- CDB: rentabilidade previsível
- Fundos de renda fixa: diversificação simples
- Ações: maior risco, potencial de retorno

## Alertas Importantes
- Gastos com cartão de crédito não devem exceder 30% da renda
- Evite parcelar compras pequenas
- Priorize quitar dívidas com juros altos
- Mantenha cadastro positivo atualizado
"""


class FinancialRetriever:
    """
    Retriever especializado em finanças.
    
    Combina:
    - Conhecimento base de finanças pessoais
    - Documentos personalizados do usuário
    - Contexto das transações do usuário
    """
    
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self.vector_store = VectorStore(collection_name="financial_knowledge")
        self.processor = DocumentProcessor()
        self.llm = LLMService()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Inicializa o retriever com conhecimento base."""
        if self._initialized:
            return
        
        stats = self.vector_store.get_stats()
        
        # Se a collection está vazia, adicionar conhecimento base
        if stats["count"] == 0:
            logger.info("Indexing base financial knowledge...")
            
            chunks = self.processor.process_text(
                FINANCIAL_KNOWLEDGE_BASE,
                metadata={"source": "base_knowledge", "type": "guide"},
            )
            
            await self.vector_store.add_chunks(chunks)
            logger.info(f"Indexed {len(chunks)} base knowledge chunks")
        
        self._initialized = True
    
    async def add_document(
        self,
        content: str,
        metadata: Optional[dict] = None,
    ) -> int:
        """
        Adiciona documento à base de conhecimento.
        
        Args:
            content: Conteúdo do documento
            metadata: Metadados opcionais
            
        Returns:
            Número de chunks criados
        """
        chunks = self.processor.process_text(content, metadata)
        await self.vector_store.add_chunks(chunks)
        return len(chunks)
    
    async def add_file(self, file_path: str) -> int:
        """
        Adiciona arquivo à base de conhecimento.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Número de chunks criados
        """
        chunks = self.processor.process_file(file_path)
        await self.vector_store.add_chunks(chunks)
        return len(chunks)
    
    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        include_base_knowledge: bool = True,
    ) -> list[dict]:
        """
        Recupera contexto relevante para a query.
        
        Args:
            query: Pergunta ou contexto
            top_k: Número de resultados
            include_base_knowledge: Se deve incluir conhecimento base
            
        Returns:
            Lista de documentos relevantes
        """
        await self.initialize()
        
        top_k = top_k or settings.rag_top_k
        
        results = await self.vector_store.search(query, top_k)
        
        return results
    
    async def retrieve_with_rerank(
        self,
        query: str,
        top_k: int = None,
        rerank_top_k: int = None,
    ) -> list[dict]:
        """
        Recupera e re-ranqueia resultados.
        
        Primeiro busca mais resultados, depois usa o LLM
        para re-ranquear e filtrar os mais relevantes.
        
        Args:
            query: Pergunta
            top_k: Número final de resultados
            rerank_top_k: Número de candidatos para rerank
            
        Returns:
            Lista de documentos relevantes re-ranqueados
        """
        top_k = top_k or settings.rag_top_k
        rerank_top_k = rerank_top_k or top_k * 2
        
        # Buscar mais candidatos
        candidates = await self.retrieve(query, top_k=rerank_top_k)
        
        if len(candidates) <= top_k:
            return candidates
        
        # Usar LLM para re-ranquear
        rerank_prompt = f"""Dada a pergunta: "{query}"

Ranqueie os seguintes documentos do mais relevante ao menos relevante.
Retorne apenas os IDs dos {top_k} documentos mais relevantes, em ordem.

Documentos:
"""
        for i, doc in enumerate(candidates):
            rerank_prompt += f"\n[{i}] {doc['content'][:200]}..."
        
        rerank_prompt += f"\n\nRetorne apenas os números dos {top_k} documentos mais relevantes, separados por vírgula."
        
        response = await self.llm.complete(
            messages=[{"role": "user", "content": rerank_prompt}],
            temperature=0.1,
            max_tokens=100,
        )
        
        try:
            # Extrair IDs do resultado
            content = response["content"]
            ids = [int(x.strip()) for x in content.split(",") if x.strip().isdigit()]
            
            # Reordenar candidatos
            reranked = []
            for idx in ids[:top_k]:
                if 0 <= idx < len(candidates):
                    reranked.append(candidates[idx])
            
            # Completar com candidatos não selecionados se necessário
            if len(reranked) < top_k:
                for doc in candidates:
                    if doc not in reranked:
                        reranked.append(doc)
                        if len(reranked) >= top_k:
                            break
            
            return reranked
            
        except Exception as e:
            logger.warning(f"Rerank failed, using original order: {e}")
            return candidates[:top_k]
    
    def format_context(self, documents: list[dict]) -> str:
        """
        Formata documentos recuperados como contexto para o LLM.
        
        Args:
            documents: Lista de documentos
            
        Returns:
            Contexto formatado como string
        """
        if not documents:
            return ""
        
        context = "## Informações Relevantes:\n\n"
        
        for i, doc in enumerate(documents, 1):
            source = doc.get("metadata", {}).get("source", "unknown")
            context += f"### Fonte {i} ({source}):\n"
            context += f"{doc['content']}\n\n"
        
        return context
    
    async def query_with_context(
        self,
        query: str,
        top_k: int = None,
    ) -> dict:
        """
        Executa query e retorna resposta com contexto.
        
        Args:
            query: Pergunta do usuário
            top_k: Número de documentos de contexto
            
        Returns:
            Dicionário com resposta e fontes
        """
        # Recuperar contexto
        documents = await self.retrieve(query, top_k)
        context = self.format_context(documents)
        
        # Gerar resposta com contexto
        system_prompt = """Você é um assistente financeiro especializado.
Use as informações fornecidas para responder à pergunta do usuário.
Se a informação não estiver disponível no contexto, use seu conhecimento geral.
Sempre cite as fontes quando usar informações do contexto."""
        
        user_prompt = f"""{context}

Pergunta: {query}

Responda de forma clara e útil, em português brasileiro."""
        
        response = await self.llm.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        return {
            "answer": response["content"],
            "sources": [
                {
                    "content": doc["content"][:200],
                    "metadata": doc.get("metadata", {}),
                    "score": doc.get("score", 0),
                }
                for doc in documents
            ],
            "tokens_used": response.get("usage", {}).get("total_tokens", 0),
        }
