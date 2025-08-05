# app/main.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import os
from contextlib import asynccontextmanager
from openai import OpenAI

# Importa a classe do módulo finder
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from finder import ServicoFinder
from reasoner import ReasonerAgent
from classifier_agent import ClassifierAgent
from web_researcher_agent import WebResearcherAgent

def get_neighborhood(df, center_index, radius=5):
    """Função auxiliar para pegar os vizinhos de um item no DataFrame."""
    start = max(0, center_index - radius)
    end = min(len(df), center_index + radius + 1)
    return df.iloc[start:end].to_dict('records')

def extract_core_keywords(query: str):
    """Usa um LLM para extrair os termos chave de uma query."""
    client = OpenAI()
    prompt = f"Extraia os 3-4 substantivos ou termos técnicos mais importantes da seguinte solicitação de construção civil: '{query}'. Retorne apenas os termos separados por espaço."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return query # Retorna a query original em caso de erro

def format_neighbor_as_result(neighbor):
    """Formata um vizinho como um item de resultado."""
    return {
        'rank': 999,  # Rank baixo para vizinhos
        'score': 0.1,  # Score baixo para vizinhos
        'semantic_score': 0.0,
        'codigo': neighbor.get('codigo', 'N/A'),
        'descricao': neighbor.get('descricao_original', neighbor.get('descricao', 'N/A')),
        'preco': neighbor.get('preco', 0.0),
        'unidade': neighbor.get('unidade', 'N/A'),
        'fonte': neighbor.get('fonte', 'N/A')
    }

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
    DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'dados', 'banco_dados_servicos.txt')
    
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
    Orquestra o fluxo de 4 agentes com um sistema de fallback em 3 estágios.
    """
    print("\n" + "="*80)
    print(f"INICIANDO PROCESSO DE BUSCA PARA: \"{query.texto_busca}\"")
    print("="*80)

    try:
        # --- TENTATIVA 1: FLUXO PADRÃO ---
        print("\n[FLUXO PRINCIPAL - TENTATIVA 1]")
        predicted_group, predicted_unit = classifier_instance.classify(query.texto_busca)
        retrieved_results, confidence_score, top_index = finder_instance.hybrid_search(
            query.texto_busca, top_k=5, predicted_group=predicted_group, predicted_unit=predicted_unit
        )
        reasoner_decision = reasoner_instance.choose_best_option(query.texto_busca, retrieved_results)
        chosen_code = reasoner_decision.get("codigo_final")

        # --- CHECKPOINT 1 ---
        if chosen_code and chosen_code != "N/A":
            print("✅ SUCESSO na Tentativa 1.")
            final_results = sorted(retrieved_results, key=lambda x: str(x['codigo']) == str(chosen_code), reverse=True)
            return {"query": query, "results": final_results[:query.top_k]}

        # --- TENTATIVA 2: FALLBACK INTERNO (PALAVRAS-CHAVE + VIZINHANÇA) ---
        print("\n[FALLBACK INTERNO - TENTATIVA 2]")
        keywords_for_retry = reasoner_decision.get("palavras_chave_para_nova_busca", query.texto_busca)
        print(f"INFO: Raciocinador falhou na 1ª tentativa. Tentando nova busca com palavras-chave: '{keywords_for_retry}'")
        
        candidate_pool = {str(item['codigo']): item for item in retrieved_results}
        
        # Busca com palavras-chave
        fallback_results, _, fallback_top_index = finder_instance.hybrid_search(keywords_for_retry, top_k=5)
        for item in fallback_results:
            candidate_pool[str(item['codigo'])] = item
            
        # Busca na vizinhança do melhor resultado do fallback
        if fallback_top_index != -1:
            neighborhood = get_neighborhood(finder_instance.dataframe, fallback_top_index, radius=10)
            for neighbor in neighborhood:
                if str(neighbor['codigo']) not in candidate_pool:
                    candidate_pool[str(neighbor['codigo'])] = format_neighbor_as_result(neighbor)
        
        final_candidates_t2 = list(candidate_pool.values())
        reasoner_decision_t2 = reasoner_instance.choose_best_option(query.texto_busca, final_candidates_t2)
        chosen_code_t2 = reasoner_decision_t2.get("codigo_final")

        # --- CHECKPOINT 2 ---
        if chosen_code_t2 and chosen_code_t2 != "N/A":
            print("✅ SUCESSO na Tentativa 2.")
            final_results = sorted(final_candidates_t2, key=lambda x: str(x['codigo']) == str(chosen_code_t2), reverse=True)
            return {"query": query, "results": final_results[:query.top_k]}

        # --- TENTATIVA 3: FALLBACK EXTERNO (PESQUISA WEB) ---
        print("\n[FALLBACK EXTERNO - TENTATIVA 3]")
        print("AVISO: Fallback interno falhou. Acionando Agente Pesquisador Web.")
        web_keywords = web_researcher_instance.research_and_enrich(query.texto_busca)
        
        if not web_keywords:
            print("❌ FALHA GERAL: Agente Web não encontrou informações. Retornando os melhores resultados da última tentativa.")
            return {"query": query, "results": final_candidates_t2[:query.top_k]}

        enriched_query = f"{query.texto_busca} {web_keywords}"
        print(f"INFO: Query enriquecida pela web: \"{enriched_query}\"")
        
        # Executa o fluxo completo com a query enriquecida
        predicted_group, predicted_unit = classifier_instance.classify(enriched_query)
        retrieved_results_t3, _, _ = finder_instance.hybrid_search(
            enriched_query, top_k=5, predicted_group=predicted_group, predicted_unit=predicted_unit
        )
        reasoner_decision_t3 = reasoner_instance.choose_best_option(enriched_query, retrieved_results_t3)
        chosen_code_t3 = reasoner_decision_t3.get("codigo_final")
        
        if chosen_code_t3 and chosen_code_t3 != "N/A":
             print("✅ SUCESSO na Tentativa 3.")
        else:
             print("❌ FALHA GERAL: Nenhuma das 3 tentativas encontrou um resultado satisfatório.")

        final_results = sorted(retrieved_results_t3, key=lambda x: str(x['codigo']) == str(chosen_code_t3), reverse=True)
        return {"query": query, "results": final_results[:query.top_k]}

    except Exception as e:
        print(f"ERRO CRÍTICO NO FLUXO PRINCIPAL: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro interno: {e}")

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "API de Busca Semântica está operacional. Use o endpoint /docs para ver a documentação interativa."}