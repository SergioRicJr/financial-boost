# 🤖💰 Financial AI Agent

Um assistente financeiro pessoal inteligente construído com **Agentes de IA**, **RAG**, **LangGraph**, e **LiteLLM**.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.0.40+-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Stack Tecnológica](#-stack-tecnológica)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [API Reference](#-api-reference)
- [Agentes e Tools](#-agentes-e-tools)
- [RAG Pipeline](#-rag-pipeline)
- [Observabilidade](#-observabilidade)
- [Desenvolvimento](#-desenvolvimento)
- [Roadmap](#-roadmap)

---

## 🎯 Visão Geral

O **Financial AI Agent** é uma aplicação que utiliza agentes de IA para ajudar usuários a gerenciar suas finanças pessoais de forma inteligente. O sistema permite:

- Conversar naturalmente sobre finanças
- Registrar e categorizar transações automaticamente
- Analisar padrões de gastos
- Receber recomendações personalizadas
- Definir e monitorar orçamentos

### Problema que Resolve

Muitas pessoas têm dificuldade em:
- 📊 Entender para onde vai seu dinheiro
- 🎯 Manter um orçamento consistente
- 🔮 Prever gastos futuros
- 💡 Identificar oportunidades de economia

O Financial AI Agent resolve esses problemas usando IA para fornecer **insights acionáveis** e **recomendações personalizadas**.

---

## ✨ Funcionalidades

### 💬 Chat Inteligente
- Conversação natural em português
- Streaming de respostas em tempo real
- Contexto mantido durante a conversa
- Suporte a múltiplos LLMs via LiteLLM

### 📝 Gestão de Transações
- Registro automático via chat
- Categorização inteligente com IA
- Busca e filtros avançados
- Tags personalizadas

### 📊 Análises Financeiras
- **Saúde Financeira**: Score de 0-100 com recomendações
- **Padrões de Gastos**: Identificação de gastos recorrentes e incomuns
- **Recomendações de Orçamento**: Baseadas na regra 50/30/20
- **Previsões**: Projeção de gastos futuros

### 🎯 Orçamentos
- Limites por categoria
- Alertas de aproximação do limite
- Comparação mês a mês
- Sugestões de ajuste

### 📚 Base de Conhecimento (RAG)
- Perguntas sobre finanças pessoais
- Dicas de investimento para iniciantes
- Explicações de conceitos financeiros
- Documentos personalizados

### 🔧 Integrações (MCP)
- Protocolo MCP para ferramentas externas
- Fácil integração com outros sistemas
- API padronizada

---

## 🏗 Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│                    (Streaming via SSE)                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI (API Gateway)                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              LangFuse (Observabilidade)                 │    │
│  │         Traces │ Prompts │ Métricas │ Custos            │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  LangGraph   │  │  MCP Server  │  │   LiteLLM    │          │
│  │  (Agentes)   │  │   (Tools)    │  │  (Gateway)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │                                     │
│  ┌─────────────────────────┴─────────────────────────────────┐  │
│  │                    Financial Tools                         │  │
│  │  • create_transaction  • get_summary    • analyze_health  │  │
│  │  • get_transactions    • set_budget     • get_patterns    │  │
│  │  • categorize         • search          • predict         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RAG PIPELINE                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Document     │  │   ChromaDB   │  │   Reranker   │          │
│  │ Processor    │  │  (Vectors)   │  │   (LLM)      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    Redis     │  │     S3       │          │
│  │  (SQLite)    │  │   (Cache)    │  │   (Files)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Stack Tecnológica

| Componente | Tecnologia | Descrição |
|------------|-----------|-----------|
| **Framework API** | FastAPI | API assíncrona de alta performance |
| **Agentes** | LangGraph | Orquestração de agentes com grafo de estados |
| **LLM Gateway** | LiteLLM | Abstração de múltiplos providers |
| **RAG** | ChromaDB / Qdrant | Vector store para embeddings |
| **Observabilidade** | LangFuse | Traces, prompts e métricas |
| **Database** | SQLAlchemy + SQLite/PostgreSQL | Persistência de dados |
| **Cache** | Redis | Cache de respostas e embeddings |
| **Tools** | MCP Protocol | Protocolo padronizado de ferramentas |

### LLMs Suportados

Via LiteLLM, o sistema suporta:
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 3, Claude 2)
- Azure OpenAI
- Google (Gemini)
- Ollama (modelos locais)
- E muitos outros...

---

## 📦 Instalação

### Pré-requisitos

- Python 3.10+
- Docker e Docker Compose (opcional)
- API Key de um provider LLM

### Instalação Local

```bash
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/financial-ai-agent.git
cd financial-ai-agent

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Copiar arquivo de configuração
cp .env.example .env

# 5. Editar .env com suas configurações
nano .env  # ou seu editor preferido

# 6. Inicializar banco de dados e dados de exemplo
python scripts/seed_data.py

# 7. Executar a aplicação
python -m app.main
# ou
uvicorn app.main:app --reload
```

### Instalação com Docker

```bash
# 1. Clonar e entrar no diretório
git clone https://github.com/seu-usuario/financial-ai-agent.git
cd financial-ai-agent

# 2. Copiar configuração
cp .env.example .env

# 3. Editar .env
nano .env

# 4. Subir todos os serviços
docker-compose up -d

# 5. Verificar logs
docker-compose logs -f app
```

A aplicação estará disponível em: http://localhost:8000

---

## ⚙️ Configuração

### Variáveis de Ambiente

Edite o arquivo `.env` com suas configurações:

```env
# Aplicação
APP_NAME="Financial AI Agent"
APP_ENV=development
DEBUG=true

# LLM - Escolha seu provider
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# API Keys (adicione a do seu provider)
OPENAI_API_KEY=sk-your-key-here
# ou
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Para usar Ollama (modelos locais)
# LLM_PROVIDER=ollama
# LLM_MODEL=llama2
# OLLAMA_BASE_URL=http://localhost:11434

# Observabilidade (opcional)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx

# Vector Store
VECTOR_STORE_TYPE=chroma
VECTOR_STORE_PATH=./data/vectors
```

### Configuração do LangFuse (Opcional)

Para habilitar observabilidade completa:

1. Crie uma conta em https://langfuse.com
2. Crie um projeto
3. Copie as chaves para o `.env`

---

## 🚀 Uso

### Interface de Chat

Acesse a documentação interativa em http://localhost:8000/docs

### Exemplos de Uso via API

#### 1. Chat Simples

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Gastei 50 reais no almoço hoje",
    "stream": false
  }'
```

#### 2. Chat com Streaming

```bash
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Como estão minhas finanças este mês?"
  }'
```

#### 3. Consulta RAG

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "O que é a regra 50/30/20?"
  }'
```

#### 4. Análise Financeira

```bash
# Resumo financeiro
curl http://localhost:8000/api/v1/analysis/summary

# Saúde financeira
curl http://localhost:8000/api/v1/analysis/health

# Padrões de gastos
curl http://localhost:8000/api/v1/analysis/patterns
```

### Exemplos de Conversas

```
Você: Gastei 150 reais no supermercado
Bot: ✅ Transação registrada com sucesso!
     📝 Descrição: Supermercado
     💰 Valor: R$ 150,00
     🏷️ Categoria: Alimentação

Você: Quanto gastei com comida esse mês?
Bot: 📊 Gastos em Alimentação - Mês Atual
     💰 Total: R$ 650,00
     📈 Média diária: R$ 21,67
     📊 vs. mês anterior: +8%
     
     Detalhamento:
     1. Supermercado - R$ 280,00 (43%)
     2. iFood - R$ 200,00 (31%)
     ...

Você: Analise minha saúde financeira
Bot: 🏥 Análise de Saúde Financeira
     📊 Score: 75/100 (Bom)
     
     ✅ Pontos Fortes:
     - Taxa de poupança acima de 30%
     - Despesas controladas
     
     ⚠️ Pontos de Atenção:
     - Gastos com alimentação acima da média
     - Sem reserva de emergência
     
     💡 Recomendações:
     1. Monte reserva de emergência
     2. Reduza gastos com delivery
```

---

## 📖 API Reference

### Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/chat` | Chat com o assistente |
| `POST` | `/api/v1/chat/stream` | Chat com streaming |
| `POST` | `/api/v1/rag/query` | Consulta base de conhecimento |
| `GET` | `/api/v1/analysis/summary` | Resumo financeiro |
| `GET` | `/api/v1/analysis/health` | Saúde financeira |
| `GET` | `/api/v1/analysis/patterns` | Padrões de gastos |
| `GET` | `/api/v1/transactions` | Listar transações |
| `POST` | `/api/v1/transactions` | Criar transação |
| `GET` | `/api/v1/categories` | Listar categorias |
| `POST` | `/api/v1/mcp/message` | Endpoint MCP |

### Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🤖 Agentes e Tools

### Arquitetura do Agente

O agente usa **LangGraph** para orquestrar a conversa:

```
┌─────────────────────────────────────────┐
│              Mensagem do Usuário        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           Agente (LangGraph)            │
│  ┌──────────────────────────────────┐   │
│  │    Decide: Responder ou Tool?    │   │
│  └──────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│   Resposta    │   │  Executa Tool │
│   Direta      │   │  (1 ou mais)  │
└───────────────┘   └───────┬───────┘
                            │
                            ▼
                  ┌───────────────┐
                  │  Retorna ao   │
                  │    Agente     │
                  └───────────────┘
```

### Tools Disponíveis

| Tool | Descrição |
|------|-----------|
| `create_transaction` | Cria nova transação |
| `get_transactions` | Lista transações |
| `get_financial_summary` | Resumo do período |
| `get_categories` | Lista categorias |
| `analyze_finances` | Análises com IA |
| `categorize_transaction` | Sugere categoria |
| `set_budget` | Define orçamento |
| `get_spending_by_category` | Gastos por categoria |
| `search_transactions` | Busca transações |

---

## 📚 RAG Pipeline

### Como Funciona

1. **Ingestão**: Documentos são processados e divididos em chunks
2. **Embeddings**: Cada chunk é convertido em vetor
3. **Armazenamento**: Vetores são salvos no ChromaDB/Qdrant
4. **Retrieval**: Busca semântica encontra chunks relevantes
5. **Geração**: LLM gera resposta com contexto

### Base de Conhecimento

O sistema vem com conhecimento sobre:
- Regra 50/30/20
- Reserva de emergência
- Categorização de gastos
- Indicadores financeiros
- Dicas de economia
- Investimentos para iniciantes

### Adicionar Documentos

```python
from app.rag.retriever import FinancialRetriever

retriever = FinancialRetriever()

# Adicionar texto
await retriever.add_document(
    content="Seu conteúdo aqui...",
    metadata={"source": "meu_documento"}
)

# Adicionar arquivo
await retriever.add_file("caminho/para/documento.pdf")
```

---

## 📊 Observabilidade

### LangFuse Dashboard

Com LangFuse habilitado, você pode monitorar:

- **Traces**: Todas as interações com o sistema
- **Latência**: Tempo de resposta de cada operação
- **Custos**: Gastos com tokens por modelo
- **Prompts**: Versionamento e A/B testing
- **Scores**: Avaliação de qualidade

### Métricas Disponíveis

- Tempo médio de resposta
- Tokens utilizados por conversa
- Taxa de uso de tools
- Erros e falhas
- Custo por usuário

---

## 🧪 Desenvolvimento

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/test_agent.py -v
```

### Linting e Formatação

```bash
# Formatação
black app tests

# Linting
ruff check app tests

# Type checking
mypy app
```

### Estrutura do Projeto

```
financial-ai-agent/
├── app/
│   ├── agents/           # Agentes LangGraph
│   │   ├── financial_agent.py
│   │   ├── tools.py
│   │   └── prompts.py
│   ├── api/              # Endpoints FastAPI
│   │   ├── routes.py
│   │   └── dependencies.py
│   ├── core/             # Configurações
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── observability.py
│   ├── db/               # Banco de dados
│   │   ├── database.py
│   │   └── models.py
│   ├── mcp/              # MCP Server
│   │   ├── server.py
│   │   └── tools.py
│   ├── rag/              # Pipeline RAG
│   │   ├── document_processor.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   ├── schemas/          # Pydantic models
│   │   ├── transaction.py
│   │   ├── chat.py
│   │   └── analysis.py
│   ├── services/         # Lógica de negócio
│   │   ├── transaction_service.py
│   │   ├── llm_service.py
│   │   └── analysis_service.py
│   └── main.py           # Aplicação FastAPI
├── data/
│   ├── knowledge_base/   # Documentos RAG
│   └── vectors/          # Vector store
├── tests/                # Testes
├── scripts/              # Scripts utilitários
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🗺 Roadmap

### Versão 1.0 (Atual)
- [x] Chat com agente financeiro
- [x] Registro de transações
- [x] Análises básicas
- [x] RAG com base de conhecimento
- [x] Observabilidade com LangFuse
- [x] MCP Server

### Versão 1.1 (Planejado)
- [ ] Autenticação JWT
- [ ] Dashboard web
- [ ] Notificações push
- [ ] Importação de extratos bancários
- [ ] Integração com Open Banking

### Versão 2.0 (Futuro)
- [ ] Multi-tenancy
- [ ] Mobile app
- [ ] Investimentos
- [ ] Metas financeiras
- [ ] Compartilhamento familiar

---

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia o [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes sobre nosso código de conduta e processo de submissão de pull requests.

---

## 📬 Contato

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/financial-ai-agent/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/financial-ai-agent/discussions)

---

<p align="center">
  Feito com ❤️ e 🤖
</p>
