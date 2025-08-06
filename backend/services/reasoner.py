# /app/reasoner.py
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class ReasonerAgent:
    """
    Agente Raciocinador com capacidade de sugerir novas buscas em caso de falha.
    """
    def __init__(self):
        self.client = OpenAI()
        self.config = self._load_config()
        self.model = self.config.get('model', 'gpt-4o-mini')
        self.base_prompt = self.config.get('base_prompt', 'Você é um engenheiro de especificações sênior, extremamente detalhista.')
        self.user_guidance_template = self.config.get('user_guidance_template', '\n\nInstrução Adicional do Especialista (prioridade máxima): {guidance}. Integre esta orientação em todos os passos de análise, sobrepondo-a ao prompt base se houver conflito.')
    
    def _load_config(self):
        """Carrega configurações do arquivo agents_config.json"""
        try:
            with open('agents_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('reasoner_agent', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"AVISO: Erro ao carregar configuração do reasoner: {e}. Usando valores padrão.")
            return {}

    def _build_expert_prompt(self, user_query: str, search_results: list[dict]) -> str:
        prompt = f"""
Você é um engenheiro de especificações sênior e detalhista. Sua tarefa é analisar a solicitação de um usuário e escolher o serviço mais adequado de uma lista de candidatos.

Siga estritamente os seguintes passos no seu raciocínio:
1. **Análise da Solicitação:** Analise a solicitação: "{user_query}". Identifique os componentes principais e as CARACTERÍSTICAS CRÍTICAS (materiais, dimensões, tipos como 'corrugado', 'manual', etc.).
2. **Avaliação dos Candidatos:** Avalie cada serviço da lista abaixo, verificando se atende às CARACTERÍSTICAS CRÍTICAS.
3. **Conclusão:** Declare qual é o serviço mais apropriado.

Sua resposta final DEVE ser um objeto JSON formatado EXATAMENTE da seguinte forma:

**Se você encontrar um serviço adequado:**
{{
  "raciocinio": "Seu texto de análise detalhada aqui.",
  "codigo_final": "O código do serviço escolhido."
}}

**Se NENHUM serviço for adequado:**
{{
  "raciocinio": "Seu texto explicando por que nenhum candidato serve.",
  "codigo_final": "N/A",
  "palavras_chave_para_nova_busca": "Liste aqui de 3 a 4 substantivos ou termos técnicos mais importantes da query original, separados por espaço. Ex: 'tubo pvc dreno'."
}}

--- SERVIÇOS CANDIDATOS ---
{json.dumps(search_results, indent=2, ensure_ascii=False)}

--- INÍCIO DA ANÁLISE E RESPOSTA JSON ---
"""
        return prompt

    def choose_best_option(self, user_query: str, search_results: list[dict]) -> dict:
        """
        Retorna um dicionário contendo a análise completa e a decisão do LLM.
        """
        if not search_results:
            return {"raciocinio": "Nenhum candidato inicial foi fornecido pelo recuperador.", "codigo_final": "N/A", "palavras_chave_para_nova_busca": user_query}
        
        prompt = self._build_expert_prompt(user_query, search_results)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            full_response_text = response.choices[0].message.content
            print(f"DEBUG: Resposta completa do LLM:\n---\n{full_response_text}\n---")
            
            result_json = json.loads(full_response_text)
            return result_json
            
        except Exception as e:
            print(f"ERRO [Agente de Raciocínio]: {e}")
            return {"raciocinio": f"Erro interno do LLM: {e}", "codigo_final": "N/A", "palavras_chave_para_nova_busca": user_query}