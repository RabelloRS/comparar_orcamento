# Sistema de Orçamento Inteligente

## 📋 Visão Geral

Sistema avançado de orçamento com busca semântica inteligente, análise de dados e interface web moderna. Utiliza IA para encontrar serviços similares em bases de dados de orçamento, com funcionalidades de classificação automática, raciocínio detalhado e pesquisa web.

## 🚀 Funcionalidades Principais

### ✅ Implementadas e Funcionando

- **🔍 Busca Semântica Avançada**: Encontra serviços similares usando embeddings e algoritmos de similaridade
- **🧠 Log de Raciocínio da IA**: Visualização detalhada do processo de pensamento da IA durante as buscas
- **🎯 Classificação Automática**: Predição inteligente de grupos e unidades de serviços
- **⚖️ Busca Híbrida**: Combinação de busca semântica e por palavras-chave com pesos otimizados
- **🚀 Sistema de Boosts**: Aplicação inteligente de relevância baseada em contexto
- **📊 Análise de Dados**: Interface para exploração e análise dos dados de orçamento
- **⚙️ Configurações**: Painel de controle para ajustes do sistema
- **🌐 Interface Web Moderna**: Frontend responsivo com Gradio
- **🔄 Cache Inteligente**: Sistema de cache para otimização de performance
- **📝 Logging Avançado**: Sistema completo de logs para monitoramento

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │────│    Backend      │────│   Serviços IA   │
│   (Gradio)      │    │   (FastAPI)     │    │  (Embeddings)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────┐            ┌─────────┐            ┌─────────┐
    │ Pages   │            │   API   │            │ Models  │
    │ Modules │            │ Routes  │            │ Cache   │
    └─────────┘            └─────────┘            └─────────┘
```

## 📁 Estrutura de Pastas

```
novo_projeto_orcamento/
├── 📄 README.md                    # Documentação principal
├── 📄 README_EXECUTAVEL.md         # Instruções para executável
├── 📄 PROTOCOLO_AGENTE.md          # Protocolo dos agentes IA
├── 📄 app_principal.py             # Aplicação principal (ponto de entrada)
├── 📄 iniciar_aplicacao.py         # Script de inicialização
├── 📄 requirements.txt             # Dependências Python
├── 📄 teste_logs.py                # Testes do sistema de logs
│
├── 🗂️ backend/                     # Backend da aplicação
│   ├── 📄 __init__.py
│   ├── 🗂️ api/                     # Camada de API
│   │   ├── 📄 __init__.py
│   │   └── 📄 routes.py            # Rotas da API REST
│   ├── 🗂️ app/                     # Aplicação principal
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py              # Configuração FastAPI
│   │   ├── 📄 classifier_agent.py  # Agente classificador
│   │   └── 📄 finder.py            # Motor de busca (legacy)
│   ├── 🗂️ core/                    # Utilitários centrais
│   │   ├── 📄 __init__.py
│   │   └── 📄 text_utils.py        # Utilitários de texto
│   └── 🗂️ services/                # Serviços de negócio
│       ├── 📄 __init__.py
│       ├── 📄 classifier_agent.py  # Classificação automática
│       ├── 📄 finder.py            # Motor de busca semântica
│       ├── 📄 reasoner.py          # Agente de raciocínio
│       └── 📄 web_researcher_agent.py # Pesquisa web
│
├── 🗂️ frontend/                    # Interface do usuário
│   ├── 📄 README_MODULAR.md        # Documentação modular
│   ├── 📄 app_modular.py           # App modular
│   ├── 📄 interface.py             # Interface principal
│   ├── 📄 interface_gradio.py      # Interface Gradio
│   └── 🗂️ pages/                   # Páginas da aplicação
│       ├── 📄 analise_dados.py     # Página de análise
│       ├── 📄 busca_semantica.py   # Página de busca
│       └── 📄 configuracoes.py     # Página de configurações
│
├── 🗂️ models/                      # Modelos treinados
│   └── 📄 classifier_pipeline.joblib # Pipeline do classificador
│
├── 🗂️ utils/                       # Utilitários gerais
│   └── 📄 logger.py                # Sistema de logging
│
├── 🗂️ logs/                        # Arquivos de log
├── 🗂️ testes/                      # Testes e validação
├── 🗂️ instrucoes/                  # Instruções e documentação
└── 🗂️ lixo/                        # Arquivos temporários
```

## 🔧 Componentes Principais

### Backend (FastAPI)

#### 📄 `backend/app/main.py`
- Configuração principal do FastAPI
- Inicialização dos serviços IA
- Configuração de CORS e middleware
- Health checks e monitoramento

#### 📄 `backend/api/routes.py`
- **Endpoint `/buscar`**: Busca semântica com log detalhado
- **Endpoint `/health`**: Verificação de saúde do sistema
- Modelos Pydantic para validação de dados
- Tratamento de erros e respostas padronizadas

#### 📄 `backend/services/finder.py`
- **Classe `ServicoFinder`**: Motor principal de busca
- **Método `hybrid_search()`**: Busca híbrida com log detalhado
- **Método `find_similar_semantic()`**: Busca por similaridade semântica
- **Método `find_similar_keyword()`**: Busca por palavras-chave (BM25)
- Sistema de cache para otimização
- Normalização e pré-processamento de texto

#### 📄 `backend/services/classifier_agent.py`
- Classificação automática de grupos e unidades
- Predição baseada em LLM
- Cache de predições para performance

#### 📄 `backend/services/reasoner.py`
- Agente de raciocínio para análise contextual
- Geração de insights sobre resultados
- Explicações detalhadas do processo

#### 📄 `backend/services/web_researcher_agent.py`
- Pesquisa web complementar
- Enriquecimento de dados
- Validação de informações

### Frontend (Gradio)

#### 📄 `app_principal.py`
- Ponto de entrada da aplicação
- Painel de controle principal
- Gerenciamento de backend
- Interface de navegação

#### 📄 `frontend/pages/busca_semantica.py`
- **Interface de busca semântica**
- **Log de raciocínio da IA**: Visualização detalhada do processo
- Configuração de parâmetros (top_k, threshold)
- Exibição de resultados em tabela
- Tratamento de erros e timeouts

#### 📄 `frontend/pages/analise_dados.py`
- Análise exploratória de dados
- Visualizações e estatísticas
- Filtros e agrupamentos

#### 📄 `frontend/pages/configuracoes.py`
- Configurações do sistema
- Ajustes de parâmetros
- Gerenciamento de cache

## 🧠 Sistema de IA

### Busca Semântica
- **Modelo**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Embeddings**: Vetores de 384 dimensões
- **Similaridade**: Cosseno com normalização
- **Cache**: Índices pré-computados para performance

### Log de Raciocínio Detalhado
O sistema agora inclui um log completo do processo de raciocínio da IA:

1. **📝 Análise da Consulta**: Processamento inicial do texto
2. **🎯 Classificação**: Predição de grupo e unidade
3. **🔍 Busca Semântica**: Cálculo de embeddings e similaridade
4. **🔤 Busca por Palavras-chave**: Algoritmo BM25
5. **⚖️ Fusão de Resultados**: Combinação ponderada
6. **🚀 Aplicação de Boosts**: Relevância contextual
7. **📊 Ranking Final**: Ordenação e seleção
8. **🎯 Preparação**: Formatação dos resultados

### Algoritmos Implementados
- **BM25**: Para busca por palavras-chave
- **Cosine Similarity**: Para busca semântica
- **Weighted Fusion**: Para combinação de resultados
- **Smart Boosting**: Para relevância contextual

## 🚀 Como Executar

### Pré-requisitos
```bash
# Python 3.8+
# Ambiente virtual recomendado
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### Instalação
```bash
# Instalar dependências
pip install -r requirements.txt
```

### Execução
```bash
# Método 1: Aplicação completa
python app_principal.py

# Método 2: Backend separado
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001

# Método 3: Script de inicialização
python iniciar_aplicacao.py
```

### URLs de Acesso
- **Frontend**: http://127.0.0.1:7861
- **Backend API**: http://127.0.0.1:8001
- **Documentação API**: http://127.0.0.1:8001/docs

## 📊 API Endpoints

### POST `/buscar`
Busca semântica com log detalhado

**Request:**
```json
{
  "texto": "concreto usinado",
  "top_k": 5,
  "threshold": 0.3
}
```

**Response:**
```json
{
  "query": "concreto usinado",
  "results": [
    {
      "rank": 1,
      "score": 0.95,
      "codigo": "04.001.001",
      "descricao": "Concreto usinado bombeável",
      "preco": 280.50,
      "unidade": "m³",
      "fonte": "SINAPI"
    }
  ],
  "detailed_reasoning": "🔍 PROCESSO DE BUSCA SEMÂNTICA...\n📝 Consulta recebida: concreto usinado..."
}
```

### GET `/health`
Verificação de saúde do sistema

## 🔧 Configurações

### Parâmetros de Busca
- **top_k**: Número máximo de resultados (padrão: 10)
- **threshold**: Limite mínimo de similaridade (padrão: 0.3)
- **semantic_weight**: Peso da busca semântica (padrão: 0.7)
- **keyword_weight**: Peso da busca por palavras-chave (padrão: 0.3)

### Cache
- **Embeddings**: Cache automático de vetores
- **Predições**: Cache de classificações
- **Resultados**: Cache de buscas frequentes

## 📈 Performance

- **Busca Semântica**: ~100ms (com cache)
- **Busca Híbrida**: ~150ms (com cache)
- **Primeira Execução**: ~5-10s (carregamento de modelos)
- **Cache Hit Rate**: >90% em uso normal

## 🧪 Testes

```bash
# Executar testes
python testes/qualitative_test.py
python testes/validator.py
```

## 📝 Logs

O sistema gera logs detalhados em:
- **Console**: Logs em tempo real
- **Arquivos**: Pasta `logs/`
- **Interface**: Log de raciocínio na busca

## 🔮 Próximas Funcionalidades

- [ ] Análise de tendências de preços
- [ ] Exportação de relatórios
- [ ] Integração com APIs externas
- [ ] Sistema de usuários e permissões
- [ ] Dashboard executivo
- [ ] Análise preditiva de custos

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

**Desenvolvido com ❤️ usando Python, FastAPI, Gradio e IA**