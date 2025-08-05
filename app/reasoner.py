# /app/reasoner.py
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class ReasonerAgent:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-4o-mini" # Modelo atualizado

    def _build_expert_prompt(self, user_query: str, search_results: list[dict]) -> str:
        prompt = f"""
        Você é um engenheiro de especificações sênior, extremamente detalhista. Sua tarefa é analisar a solicitação de um usuário e escolher o serviço mais adequado de uma lista de candidatos, prestando atenção máxima às características técnicas.

        **Regra Principal:** Adjetivos que definem uma propriedade física, material ou tipo (ex: 'corrugado', 'rígido', 'estrutural', 'manual', 'mecanizado') são CRÍTICOS e devem ter um peso maior na sua decisão.

        Siga estritamente os seguintes passos no seu raciocínio:
        1. **Análise da Solicitação:** Analise a solicitação: "{user_query}". Identifique os componentes principais e, mais importante, as CARACTERÍSTICAS CRÍTICAS (materiais, dimensões, tipos).
        2. **Avaliação dos Candidatos:** Avalie cada serviço da lista abaixo. Para cada um, verifique explicitamente se ele atende ou não às CARACTERÍSTICAS CRÍTICAS identificadas.
        3. **Conclusão:** Declare qual é o serviço mais apropriado. Se um candidato corresponde às características críticas, ele deve ser preferido, mesmo que outros termos sejam ligeiramente diferentes. Se nenhum candidato atender às características críticas, declare que nenhum é adequado.

        Após o seu raciocínio, sua resposta final DEVE ser um objeto JSON formatado EXATAMENTE da seguinte forma:
        {{
          "raciocinio": "Seu texto de análise detalhada aqui, seguindo os 3 passos.",
          "codigo_final": "O código do serviço escolhido aqui. Se nenhum for adequado, retorne 'N/A'."
        }}

        --- SERVIÇOS CANDIDATOS ---
        {json.dumps(search_results, indent=2, ensure_ascii=False)}
        
        --- INÍCIO DA ANÁLISE E RESPOSTA JSON ---
        """
        return prompt

    def choose_best_option(self, user_query: str, search_results: list[dict]) -> str | None:
        if not search_results: return None
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
            chosen_code = result_json.get("codigo_final")
            
            return chosen_code if chosen_code != "N/A" else None
        except Exception as e:
            print(f"ERRO [Agente de Raciocínio]: {e}")
            return None