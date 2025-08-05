# 🏗️ Assistente de Orçamento de Obras Públicas

Sistema inteligente para busca e análise de serviços de construção civil usando IA e busca semântica.

## 📋 Funcionalidades

### 1. Busca Semântica Inteligente
- Busca por contexto, sinônimos ou descrições incompletas
- Sistema de agentes IA para análise refinada
- Resultados com código, descrição, preço e fonte

### 2. Filtro Rápido em Tempo Real
- Filtragem instantânea do banco de dados completo
- Busca por qualquer parte do nome do serviço
- Interface responsiva e rápida

### 3. Processamento de Planilhas em Lote
- Upload de planilhas Excel (.xlsx)
- Processamento automático de múltiplas descrições
- Download da planilha processada com códigos e preços

## 🚀 Como Usar

### Opção 1: Script de Inicialização (Recomendado)

```bash
python iniciar_aplicacao.py
```

Escolha a opção 1 para iniciar a aplicação completa.

### Opção 2: Inicialização Manual

#### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

#### 2. Iniciar o Backend
```bash
cd app
python -m uvicorn main:app --reload --port 8000
```

#### 3. Iniciar o Frontend (em outro terminal)
```bash
streamlit run interface.py
```

## 📁 Estrutura do Projeto

```
├── app/                          # Backend FastAPI
│   ├── main.py                   # API principal
│   ├── finder.py                 # Motor de busca
│   ├── reasoner.py              # Agente de raciocínio
│   ├── classifier_agent.py      # Agente classificador
│   └── web_researcher_agent.py  # Agente de pesquisa web
├── dados/                        # Dados da aplicação
│   └── banco_dados_servicos.txt  # Base de dados de serviços
├── interface.py                  # Interface Streamlit
├── iniciar_aplicacao.py         # Script de inicialização
├── requirements.txt             # Dependências Python
└── README.md                    # Este arquivo
```

## 🔧 Dependências Principais

- **Streamlit**: Interface web interativa
- **FastAPI**: Backend API REST
- **Pandas**: Manipulação de dados
- **Requests**: Comunicação HTTP
- **OpenAI**: Integração com modelos de IA
- **Sentence Transformers**: Embeddings semânticos
- **Uvicorn**: Servidor ASGI

## 📊 Como Usar a Interface

### Busca Semântica
1. Digite uma descrição do serviço desejado
2. Ajuste o número de resultados (1-10)
3. Clique em "Buscar com IA"
4. Analise os resultados com códigos, preços e fontes

### Filtro Rápido
1. Digite qualquer parte do nome do serviço
2. A lista será filtrada automaticamente
3. Navegue pelos resultados em tempo real

### Processamento de Planilhas
1. Prepare uma planilha Excel com coluna 'descricao'
2. Faça o upload do arquivo
3. Clique em "Processar Planilha Completa"
4. Baixe o resultado processado

## ⚠️ Requisitos do Sistema

- Python 3.8 ou superior
- Conexão com internet (para agentes de IA)
- Chave API OpenAI configurada (variável de ambiente)
- Pelo menos 4GB de RAM disponível

## 🔑 Configuração de API Keys

Crie um arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sua_chave_openai_aqui
BRAVE_API_KEY=sua_chave_brave_aqui  # Opcional
SERPAPI_KEY=sua_chave_serpapi_aqui  # Opcional
```

## 🐛 Solução de Problemas

### Backend não inicia
- Verifique se todas as dependências estão instaladas
- Confirme se a porta 8000 não está em uso
- Verifique se as chaves de API estão configuradas

### Interface não conecta ao backend
- Certifique-se de que o backend está rodando
- Verifique se a URL da API está correta (http://localhost:8000)
- Aguarde alguns segundos após iniciar o backend

### Erro ao carregar banco de dados
- Verifique se o arquivo `dados/banco_dados_servicos.txt` existe
- Confirme se o arquivo está no formato CSV correto
- Verifique as permissões de leitura do arquivo

### Processamento de planilha falha
- Certifique-se de que o backend está rodando
- Verifique se a planilha tem a coluna 'descricao'
- Confirme se o arquivo está no formato .xlsx

## 📈 Status da Aplicação

A interface mostra o status da conexão com o backend:
- 🟢 **API conectada e funcionando**: Tudo operacional
- 🟡 **API respondendo com problemas**: Backend com issues
- 🔴 **API desconectada**: Backend não está rodando

## 🤝 Suporte

Para problemas ou dúvidas:
1. Verifique a seção de solução de problemas
2. Consulte os logs do terminal
3. Verifique se todas as dependências estão atualizadas

## 📝 Notas Importantes

- O sistema requer conexão com internet para funcionalidades de IA
- O processamento de planilhas grandes pode demorar alguns minutos
- Mantenha o backend rodando durante o uso da interface
- Os resultados são baseados no banco de dados de serviços disponível

---

**Desenvolvido para facilitar a busca e análise de serviços de construção civil em obras públicas.**