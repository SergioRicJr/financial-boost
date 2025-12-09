"""
Document Processor
==================

Processa documentos para indexação no sistema RAG.
"""

import hashlib
import os
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from app.core.config import settings


class Document:
    """Representa um documento processado."""
    
    def __init__(
        self,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ):
        self.content = content
        self.metadata = metadata or {}
        self.doc_id = doc_id or self._generate_id()
    
    def _generate_id(self) -> str:
        """Gera ID único baseado no conteúdo."""
        return hashlib.md5(self.content.encode()).hexdigest()[:12]
    
    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Document(id={self.doc_id}, content='{preview}')"


class Chunk:
    """Representa um chunk de documento."""
    
    def __init__(
        self,
        content: str,
        metadata: dict[str, Any],
        chunk_id: str,
        doc_id: str,
    ):
        self.content = content
        self.metadata = metadata
        self.chunk_id = chunk_id
        self.doc_id = doc_id


class DocumentProcessor:
    """
    Processa documentos para o pipeline RAG.
    
    Suporta:
    - Arquivos de texto (.txt, .md)
    - PDFs
    - Documentos Word (.docx)
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap
    
    def process_file(self, file_path: str) -> list[Chunk]:
        """
        Processa um arquivo e retorna chunks.
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            Lista de chunks processados
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        extension = path.suffix.lower()
        
        if extension in [".txt", ".md"]:
            content = self._read_text_file(path)
        elif extension == ".pdf":
            content = self._read_pdf_file(path)
        elif extension == ".docx":
            content = self._read_docx_file(path)
        else:
            raise ValueError(f"Formato não suportado: {extension}")
        
        document = Document(
            content=content,
            metadata={
                "source": str(path),
                "filename": path.name,
                "extension": extension,
            }
        )
        
        return self.chunk_document(document)
    
    def process_text(
        self,
        text: str,
        metadata: Optional[dict] = None,
    ) -> list[Chunk]:
        """
        Processa texto diretamente.
        
        Args:
            text: Texto para processar
            metadata: Metadados opcionais
            
        Returns:
            Lista de chunks
        """
        document = Document(content=text, metadata=metadata)
        return self.chunk_document(document)
    
    def chunk_document(self, document: Document) -> list[Chunk]:
        """
        Divide documento em chunks.
        
        Usa estratégia de divisão por parágrafos quando possível,
        com fallback para divisão por caracteres.
        """
        content = document.content
        chunks = []
        
        # Tentar dividir por parágrafos primeiro
        paragraphs = content.split("\n\n")
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Se adicionar este parágrafo exceder o limite
            if len(current_chunk) + len(para) + 2 > self.chunk_size:
                # Salvar chunk atual se não estiver vazio
                if current_chunk:
                    chunks.append(self._create_chunk(
                        content=current_chunk,
                        document=document,
                        index=chunk_index,
                    ))
                    chunk_index += 1
                
                # Se o parágrafo sozinho é maior que o chunk_size
                if len(para) > self.chunk_size:
                    # Dividir o parágrafo em pedaços menores
                    sub_chunks = self._split_long_text(para)
                    for sub_chunk in sub_chunks:
                        chunks.append(self._create_chunk(
                            content=sub_chunk,
                            document=document,
                            index=chunk_index,
                        ))
                        chunk_index += 1
                    current_chunk = ""
                else:
                    current_chunk = para
            else:
                # Adicionar parágrafo ao chunk atual
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Salvar último chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                content=current_chunk,
                document=document,
                index=chunk_index,
            ))
        
        logger.info(f"Document {document.doc_id} split into {len(chunks)} chunks")
        return chunks
    
    def _split_long_text(self, text: str) -> list[str]:
        """Divide texto longo em pedaços menores."""
        chunks = []
        
        # Tentar dividir por sentenças
        sentences = text.replace("? ", "?\n").replace("! ", "!\n").replace(". ", ".\n").split("\n")
        
        current = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current) + len(sentence) + 1 > self.chunk_size:
                if current:
                    chunks.append(current)
                current = sentence
            else:
                if current:
                    current += " " + sentence
                else:
                    current = sentence
        
        if current:
            chunks.append(current)
        
        return chunks
    
    def _create_chunk(
        self,
        content: str,
        document: Document,
        index: int,
    ) -> Chunk:
        """Cria um objeto Chunk."""
        return Chunk(
            content=content,
            metadata={
                **document.metadata,
                "chunk_index": index,
            },
            chunk_id=f"{document.doc_id}_{index}",
            doc_id=document.doc_id,
        )
    
    def _read_text_file(self, path: Path) -> str:
        """Lê arquivo de texto."""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def _read_pdf_file(self, path: Path) -> str:
        """Lê arquivo PDF."""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(str(path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            logger.warning("pypdf not installed. PDF reading disabled.")
            raise ImportError("Install pypdf to read PDF files: pip install pypdf")
    
    def _read_docx_file(self, path: Path) -> str:
        """Lê arquivo Word."""
        try:
            from docx import Document as DocxDocument
            
            doc = DocxDocument(str(path))
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except ImportError:
            logger.warning("python-docx not installed. DOCX reading disabled.")
            raise ImportError("Install python-docx to read Word files: pip install python-docx")
