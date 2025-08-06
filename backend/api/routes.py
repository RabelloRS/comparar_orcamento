# api/routes.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List

# Importa os serviços
from backend.services.finder import ServicoFinder
from backend.services.reasoner import ReasonerAgent
from backend.services.classifier_agent import ClassifierAgent
from backend.services.web_researcher_agent import WebResearcherAgent
from backend.core.text_utils import extract_core_keywords, get_neighborhood, format_neighbor_as_result

# Modelos Pydantic
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
    results: List[SearchResultItem]
    detailed_reasoning: str = Field(default="", description="Log detalhado do processo de raciocínio da IA")

# Router
router = APIRouter()

# Instâncias globais dos serviços (serão inicializadas no main.py)
finder_instance = None
reasoner_instance = None
classifier_instance = None
web_researcher_instance = None

def set_service_instances(finder, reasoner, classifier, web_researcher):
    """Define as instâncias dos serviços."""
    global finder_instance, reasoner_instance, classifier_instance, web_researcher_instance
    finder_instance = finder
    reasoner_instance = reasoner
    classifier_instance = classifier
    web_researcher_instance = web_researcher

@router.post("/buscar",
             response_model=SearchResponse,
             tags=["Busca Semântica com Agente"],
             summary="Realiza uma busca semântica refinada por um agente de IA")
async def buscar_servicos(query: SearchQuery):
    """Endpoint principal para busca semântica de serviços."""
    try:
        if not all([finder_instance, reasoner_instance, classifier_instance, web_researcher_instance]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Serviços não inicializados"
            )
        
        # Extrai palavras-chave da query
        core_keywords = extract_core_keywords(query.texto_busca)
        
        # Classifica a query
        predicted_group, predicted_unit = classifier_instance.classify(query.texto_busca)
        
        # Busca inicial com log detalhado
        initial_results, score_semantico, indice_original, detailed_reasoning = finder_instance.hybrid_search(
            query.texto_busca, 
            top_k=min(query.top_k * 2, 10),
            predicted_group=predicted_group,
            predicted_unit=predicted_unit
        )
        
        if not initial_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum serviço encontrado para a busca especificada"
            )
        
        # Raciocínio com LLM
        reasoning_result = reasoner_instance.choose_best_option(
            query.texto_busca,
            initial_results
        )
        
        # Verifica se precisa de nova busca
        if reasoning_result.get("codigo_final") == "N/A" and "palavras_chave_para_nova_busca" in reasoning_result:
            # Nova busca com palavras-chave refinadas
            new_query = reasoning_result["palavras_chave_para_nova_busca"]
            initial_results, _, _, additional_reasoning = finder_instance.hybrid_search(new_query, top_k=query.top_k)
            # Adiciona o log da segunda busca ao reasoning detalhado
            detailed_reasoning += "\n\n🔄 **SEGUNDA BUSCA COM PALAVRAS-CHAVE REFINADAS**\n" + additional_reasoning
        
        # Limita aos top_k solicitados
        final_results = initial_results[:query.top_k]
        
        # Adiciona vizinhos se necessário
        if len(final_results) < query.top_k:
            needed = query.top_k - len(final_results)
            df = finder_instance.df
            
            for result in final_results:
                try:
                    idx = df[df['codigo'] == result['codigo']].index[0]
                    neighbors = get_neighborhood(df, idx, radius=2)
                    
                    for neighbor in neighbors:
                        if len(final_results) >= query.top_k:
                            break
                        if neighbor['codigo'] not in [r['codigo'] for r in final_results]:
                            final_results.append(format_neighbor_as_result(neighbor))
                            needed -= 1
                            if needed <= 0:
                                break
                    
                    if needed <= 0:
                        break
                except (IndexError, KeyError):
                    continue
        
        return SearchResponse(
            query=query,
            results=final_results,
            detailed_reasoning=detailed_reasoning
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@router.get("/health",
           tags=["Sistema"],
           summary="Verifica o status dos serviços")
async def health_check():
    """Endpoint para verificar a saúde dos serviços."""
    services_status = {
        "finder": finder_instance is not None,
        "reasoner": reasoner_instance is not None,
        "classifier": classifier_instance is not None,
        "web_researcher": web_researcher_instance is not None
    }
    
    all_healthy = all(services_status.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "services": services_status
    }