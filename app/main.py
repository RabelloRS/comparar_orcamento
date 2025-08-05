# app/main.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import os
from contextlib import asynccontextmanager

# Importa a classe do módulo finder
from .finder import ServicoFinder
from .reasoner import ReasonerAgent
from .classifier_agent import ClassifierAgent
from .web_researcher_agent import WebResearcherAgent

# --- Modelos de Dados para a API ---
class SearchQuery(BaseModel):
    texto_busca: str = Field(..., min_length=3, example="concreto usinado 30mpa")
    top_k: int = Field(3, gt=0, le=10, example=3)

class SearchResultItem(BaseModel):
    rank: int
    score: float
    codigo: str
    descricao: str
    preco: float
    unidade: str
    fonte: str

class SearchResponse(BaseModel):
    query: SearchQuery
    results: list[SearchResultItem]


# --- Lógica de Inicialização e Ciclo de Vida da API ---
# Instâncias globais
finder_instance = None
reasoner_instance = None
classifier_instance = None
web_researcher_instance = None
CONFIDENCE_THRESHOLD = 0.7  # Limiar de confiança para acionar a pesquisa web
# DATA_FILE_PATH será determinado automaticamente pelo finder

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Função para gerenciar o ciclo de vida da aplicação.
    Carrega o modelo na inicialização.
    """
    print("INFO: Iniciando a aplicação...")
    
    global finder_instance, reasoner_instance, classifier_instance, web_researcher_instance
    finder_instance = ServicoFinder()
    finder_instance.load_and_index_services()  # Carregamento automático da base otimizada
    
    print("INFO: Inicializando o agente de raciocínio...")
    reasoner_instance = ReasonerAgent()
    print("INFO: Agente de raciocínio inicializado com sucesso.")
    
    print("INFO: Inicializando o agente classificador...")
    # Usa o mesmo caminho que o finder determinou
    if os.path.exists('dados/knowledge_base_fixed.csv'):
        base_path = 'dados/knowledge_base_fixed.csv'
    elif os.path.exists('dados/knowledge_base_optimized.csv'):
        base_path = 'dados/knowledge_base_optimized.csv'
    else:
        base_path = 'dados/knowledge_base.csv'
    classifier_instance = ClassifierAgent(data_filepath=base_path)
    print("INFO: Agente classificador inicializado com sucesso.")
    
    print("INFO: Inicializando o agente de pesquisa web...")
    web_researcher_instance = WebResearcherAgent()
    print("INFO: Agente de pesquisa web inicializado com sucesso.")
    
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


# --- Endpoint da API ---
@app.post("/buscar",
          response_model=SearchResponse,
          tags=["Busca Semântica com Agente"],
          summary="Realiza uma busca semântica refinada por um agente de IA")
async def buscar_servicos(query: SearchQuery):
    """
    Fluxo RAG com 4 agentes e logging de diagnóstico detalhado.
    VERSÃO CORRIGIDA da orquestração dos agentes.
    """
    print("\n" + "="*80)
    print(f"INICIANDO DIAGNÓSTICO PARA QUERY: \"{query.texto_busca}\"")
    print("="*80)

    try:
        # --- ETAPA 1: Classificação Inicial ---
        print("\n[AGENTE 1: CLASSIFICADOR] - INÍCIO")
        predicted_group, predicted_unit = classifier_instance.classify(query.texto_busca)
        print(f"[AGENTE 1: CLASSIFICADOR] - FIM -> Grupo: '{predicted_group}', Unidade: '{predicted_unit}'")

        # --- ETAPA 2: Recuperação Inicial ---
        print("\n[AGENTE 2: RECUPERADOR HÍBRIDO] - INÍCIO (Tentativa 1)")
        # A variável final que o Raciocinador usará
        final_retrieved_results, confidence_score = finder_instance.hybrid_search(
            query.texto_busca, top_k=5, predicted_group=predicted_group, predicted_unit=predicted_unit
        )
        query_para_raciocinio = query.texto_busca
        print(f"[AGENTE 2: RECUPERADOR HÍBRIDO] - FIM -> {len(final_retrieved_results)} itens recuperados.")

        # --- ETAPA 3: Verificação de Confiança e Fallback (se necessário) ---
        print(f"\n[VERIFICAÇÃO DE CONFIANÇA] -> Score Semântico: {confidence_score:.4f}, Limiar: {CONFIDENCE_THRESHOLD}")
        
        if confidence_score < CONFIDENCE_THRESHOLD:
            print("[VERIFICAÇÃO DE CONFIANÇA] -> BAIXA CONFIANÇA. Acionando Agente 4 (Pesquisador Web).")
            
            # --- AGENTE 4: PESQUISADOR WEB ---
            web_keywords = web_researcher_instance.research_and_enrich(query.texto_busca)
            
            if web_keywords:
                enriched_query = f"{query.texto_busca} {web_keywords}"
                query_para_raciocinio = enriched_query # Atualiza a query para o Raciocinador
                print(f"INFO: Query enriquecida: \"{enriched_query}\"")
                print("\n--- REINICIANDO BUSCA (Tentativa 2) ---")
                
                # Re-classifica e Re-busca com a query enriquecida
                predicted_group, predicted_unit = classifier_instance.classify(enriched_query)
                final_retrieved_results, _ = finder_instance.hybrid_search(
                    enriched_query, top_k=5, predicted_group=predicted_group, predicted_unit=predicted_unit
                )
                print(f"--- FIM DA TENTATIVA 2 -> {len(final_retrieved_results)} novos itens recuperados. ---")
        else:
            print("[VERIFICAÇÃO DE CONFIANÇA] -> ALTA CONFIANÇA. Fluxo concluído na primeira tentativa.")

        # --- ETAPA FINAL: Raciocínio (Sempre executado por último) ---
        print("\n[AGENTE 3: AGENTE DE RACIOCÍNIO] - INÍCIO")
        if not final_retrieved_results:
             print("[AGENTE 3: AGENTE DE RACIOCÍNIO] - AVISO: Não há resultados para analisar.")
             chosen_code = None
        else:
            chosen_code = reasoner_instance.choose_best_option(query_para_raciocinio, final_retrieved_results)
        print(f"[AGENTE 3: AGENTE DE RACIOCÍNIO] - FIM -> Código escolhido: {chosen_code}")

        # Re-organiza os resultados finais com base na escolha final do Raciocinador
        final_sorted_results = sorted(final_retrieved_results, key=lambda x: str(x['codigo']) == str(chosen_code), reverse=True)

        print("\n" + "="*80)
        print("DIAGNÓSTICO COMPLETO FINALIZADO")
        print("="*80 + "\n")

        return {"query": query, "results": final_sorted_results[:query.top_k]}

    except Exception as e:
        print(f"ERRO CRÍTICO NO FLUXO PRINCIPAL: {e}")
        import traceback
        traceback.print_exc() # Imprime o stacktrace completo do erro no console do servidor
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno: {e}")

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "API de Busca Semântica está operacional. Use o endpoint /docs para ver a documentação interativa."}