# app/main.py
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import os
from contextlib import asynccontextmanager
from openai import OpenAI

# Importa a classe do módulo finder
from .finder import ServicoFinder
from .reasoner import ReasonerAgent
from .classifier_agent import ClassifierAgent
from .web_researcher_agent import WebResearcherAgent

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

        # --- TENTATIVA 1: FLUXO COMPLETO ---
        print("\n--- INICIANDO BUSCA PARA: \"{query.texto_busca}\" ---")
        retrieved_results, confidence_score, top_index = finder_instance.hybrid_search(
            query.texto_busca, top_k=5, predicted_group=predicted_group, predicted_unit=predicted_unit
        )

        candidate_pool = {str(item['codigo']): item for item in retrieved_results}

        # --- LÓGICA DE BUSCA NA VIZINHANÇA ---
        if top_index != -1:
            print(f"INFO: Melhor candidato inicial no índice {top_index}. Buscando vizinhança...")
            neighborhood = get_neighborhood(finder_instance.dataframe, top_index, radius=5)
            for neighbor in neighborhood:
                # Adiciona ao pool de candidatos, evitando duplicatas
                if str(neighbor['codigo']) not in candidate_pool:
                    candidate_pool[str(neighbor['codigo'])] = format_neighbor_as_result(neighbor)

        # --- LÓGICA DE FALLBACK POR PALAVRAS-CHAVE ---
        if confidence_score < 0.6: # Usamos um limiar mais baixo para este fallback
            print(f"AVISO: Confiança muito baixa ({confidence_score:.2f}). Tentando fallback com palavras-chave.")
            core_keywords = extract_core_keywords(query.texto_busca)
            print(f"INFO: Palavras-chave extraídas: '{core_keywords}'")
            
            # Executa uma busca mais simples, sem boosts, apenas com as palavras-chave
            fallback_results, _, _ = finder_instance.hybrid_search(core_keywords, top_k=5)
            for item in fallback_results:
                if str(item['codigo']) not in candidate_pool:
                    candidate_pool[str(item['codigo'])] = item

        # --- AGENTE DE RACIOCÍNIO FINAL ---
        final_candidates = list(candidate_pool.values())
        print(f"INFO: Enviando {len(final_candidates)} candidatos únicos para o Agente de Raciocínio.")
        query_para_raciocinio = query.texto_busca

        # --- ETAPA FINAL: Raciocínio (Sempre executado por último) ---
        print("\n[AGENTE 3: AGENTE DE RACIOCÍNIO] - INÍCIO")
        if not final_candidates:
             print("[AGENTE 3: AGENTE DE RACIOCÍNIO] - AVISO: Não há resultados para analisar.")
             chosen_code = None
        else:
            chosen_code = reasoner_instance.choose_best_option(query_para_raciocinio, final_candidates)
        print(f"[AGENTE 3: AGENTE DE RACIOCÍNIO] - FIM -> Código escolhido: {chosen_code}")

        # Re-organiza os resultados finais com base na escolha final do Raciocinador
        final_sorted_results = sorted(final_candidates, key=lambda x: str(x['codigo']) == str(chosen_code), reverse=True)

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