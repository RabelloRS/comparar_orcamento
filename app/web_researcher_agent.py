# /app/web_researcher_agent.py
import os
import json
from serpapi import GoogleSearch
from openai import OpenAI

class WebResearcherAgent:
    """
    Agente que busca na internet para enriquecer queries de baixa confiança.
    Gerencia múltiplas APIs de busca e seus limites.
    """
    def __init__(self):
        # Carrega as chaves do ambiente
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        # (A integração com Zyte pode ser adicionada de forma similar se necessário)

        self.llm_client = OpenAI() # Reutiliza a chave da OpenAI já configurada

        # Simples monitoramento de uso em memória (para uma aplicação real, usar um banco de dados ou cache como Redis)
        self.usage_counters = {'brave': 0, 'serpapi': 0}
        self.usage_limits = {'brave': 2000, 'serpapi': 250}
        print("INFO: Agente Pesquisador Web inicializado.")

    def _search_brave(self, query: str):
        if self.brave_api_key and self.usage_counters['brave'] < self.usage_limits['brave']:
            print("DEBUG [Pesquisador Web]: Usando Brave Search API...")
            self.usage_counters['brave'] += 1
            try:
                # Implementação simplificada para Brave Search
                # Como a biblioteca brave-search pode ter diferentes implementações,
                # vamos usar uma abordagem mais genérica
                import requests
                headers = {'X-Subscription-Token': self.brave_api_key}
                params = {'q': query, 'count': 3}
                response = requests.get('https://api.search.brave.com/res/v1/web/search', 
                                      headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return [res.get('description', '') for res in data.get('web', {}).get('results', [])[:3]]
            except Exception as e:
                print(f"ERRO [Pesquisador Web]: Falha no Brave Search: {e}")
        return None

    def _search_serpapi(self, query: str):
        if self.serpapi_api_key and self.usage_counters['serpapi'] < self.usage_limits['serpapi']:
            print("DEBUG [Pesquisador Web]: Usando SerpApi...")
            self.usage_counters['serpapi'] += 1
            try:
                params = {"engine": "google", "q": query, "api_key": self.serpapi_api_key}
                search = GoogleSearch(params)
                results = search.get_dict()
                return [res.get('snippet', '') for res in results.get("organic_results", [])[:3]]
            except Exception as e:
                print(f"ERRO [Pesquisador Web]: Falha no SerpApi: {e}")
        return None
        
    def _summarize_and_extract_keywords(self, snippets: list[str], original_query: str) -> str:
        """Usa um LLM para extrair palavras-chave relevantes dos snippets da web."""
        if not snippets:
            return ""

        context = "\n".join(snippets)
        prompt = f"""
        A consulta original do usuário foi: "{original_query}".
        O seguinte texto foi recuperado de uma busca na internet:
        ---
        {context}
        ---
        Com base no texto acima, extraia 5 a 7 palavras-chave técnicas ou termos adicionais que são altamente relevantes para a consulta original e que poderiam ajudar a refinar uma nova busca em um banco de dados de construção civil. Retorne apenas as palavras-chave separadas por vírgula.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            keywords = response.choices[0].message.content.strip()
            print(f"DEBUG [Pesquisador Web]: Palavras-chave extraídas da web: {keywords}")
            return keywords
        except Exception as e:
            print(f"ERRO [Pesquisador Web]: Falha na extração de palavras-chave: {e}")
            return ""

    def research_and_enrich(self, query: str) -> str:
        """
        Orquestra a busca na web e o enriquecimento da query.
        """
        print(f"INFO [Pesquisador Web]: Iniciando pesquisa na web para a query: '{query}'")
        snippets = self._search_brave(query)
        
        if not snippets:
            snippets = self._search_serpapi(query)
            
        # (Adicionar aqui a lógica para o Zyte se necessário)

        if not snippets:
            print("AVISO [Pesquisador Web]: Todas as APIs de busca falharam ou atingiram o limite.")
            return ""
            
        enriched_keywords = self._summarize_and_extract_keywords(snippets, query)
        
        return enriched_keywords