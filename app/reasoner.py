# /app/reasoner.py
import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class ReasonerAgent:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-3.5-turbo"

    def _build_cot_prompt(self, user_query: str, search_results: list[dict]) -> str:
        prompt = f"""
        Você é um engenheiro orçamentista sênior. Sua tarefa é analisar a solicitação do usuário e os serviços candidatos encontrados em nosso banco de dados, e escolher o serviço mais adequado.

        Siga estritamente os seguintes passos no seu raciocínio:
        1. **Análise da Solicitação:** Analise a solicitação: "{user_query}". Identifique os componentes, materiais e ações mais importantes.
        2. **Avaliação dos Candidatos:** Avalie cada serviço da lista abaixo, comparando-o com sua análise.
        3. **Conclusão:** Declare qual é o serviço mais apropriado.

        Após o seu raciocínio, sua resposta final DEVE ser um objeto JSON formatado EXATAMENTE da seguinte forma:
        {{
          "raciocinio": "Seu texto de análise detalhada aqui.",
          "codigo_final": "O código do serviço escolhido aqui. Se nenhum for adequado, retorne 'N/A'."
        }}

        --- SERVIÇOS CANDIDATOS ---
        {json.dumps(search_results, indent=2, ensure_ascii=False)}
        
        --- INÍCIO DA ANÁLISE E RESPOSTA JSON ---
        """
        return prompt

    def choose_best_option(self, user_query: str, search_results: list[dict]) -> str | None:
        if not search_results: return None
        prompt = self._build_cot_prompt(user_query, search_results)
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
            chosen_code = result_json.get("codigo_final")
            
            return chosen_code if chosen_code != "N/A" else None
        except Exception as e:
            print(f"ERRO [Agente de Raciocínio]: {e}")
            return None