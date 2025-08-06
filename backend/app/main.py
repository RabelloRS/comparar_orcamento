# app/main.py
from fastapi import FastAPI
import os
from contextlib import asynccontextmanager

# Importa os serviços da nova estrutura
import sys
import os

# Adiciona o diretório raiz do projeto ao path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.services.finder import ServicoFinder
from backend.services.reasoner import ReasonerAgent
from backend.services.classifier_agent import ClassifierAgent
from backend.services.web_researcher_agent import WebResearcherAgent
from backend.api.routes import router, set_service_instances

# --- Lógica de Inicialização e Ciclo de Vida da API ---
# Instâncias globais
finder_instance = None
reasoner_instance = None
classifier_instance = None
web_researcher_instance = None

# DATA_FILE_PATH será determinado automaticamente pelo finder

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Função para gerenciar o ciclo de vida da aplicação.
    Carrega o modelo na inicialização.
    """
    print("INFO: Iniciando a aplicação...")
    
    global finder_instance, reasoner_instance, classifier_instance, web_researcher_instance
    
    # Aponte o Finder para o banco de dados principal e bruto
    DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'dados', 'banco_dados_servicos.txt')
    
    finder_instance = ServicoFinder()
    finder_instance.load_and_index_services(data_filepath=DATA_FILE_PATH)
    
    print("INFO: Inicializando o agente de raciocínio...")
    reasoner_instance = ReasonerAgent()
    print("INFO: Agente de raciocínio inicializado com sucesso.")
    
    print("INFO: Inicializando o agente classificador...")
    # Usa o mesmo arquivo de dados principal
    classifier_instance = ClassifierAgent(data_filepath=DATA_FILE_PATH)
    print("INFO: Agente classificador inicializado com sucesso.")
    
    print("INFO: Inicializando o agente de pesquisa web...")
    web_researcher_instance = WebResearcherAgent()
    print("INFO: Agente de pesquisa web inicializado com sucesso.")
    
    # Define as instâncias dos serviços no router
    set_service_instances(finder_instance, reasoner_instance, classifier_instance, web_researcher_instance)
    
    print("INFO: Aplicação pronta para receber requisições.")
    yield
    # Código de limpeza (se necessário) ao desligar a aplicação
    print("INFO: Encerrando a aplicação...")


# --- Criação da Aplicação FastAPI ---
app = FastAPI(
    title="API de Busca Semântica de Serviços",
    description="Uma API para encontrar serviços de construção civil usando busca semântica.",
    version="1.0.0",
    lifespan=lifespan
)

# Inclui as rotas
app.include_router(router)


# Endpoints são definidos em backend/api/routes.py

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "API de Busca Semântica está operacional. Use o endpoint /docs para ver a documentação interativa."}