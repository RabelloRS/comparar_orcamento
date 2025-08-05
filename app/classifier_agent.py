# /app/classifier_agent.py
import pandas as pd
import os
import json
from openai import OpenAI

class ClassifierAgent:
    """
    Usa um LLM (gpt-3.5-turbo) para realizar uma classificação de alta precisão.
    """
    def __init__(self, data_filepath):
        self.client = OpenAI() # Reutiliza a chave do .env
        self.model = "gpt-4o-mini"
        
        # Carrega os grupos e unidades ÚNICOS para dar como opções ao LLM
        df = pd.read_csv(data_filepath)
        self.grupos_unicos = df['descricao_do_grupo_de_servico'].dropna().unique().tolist()
        self.unidades_unicas = df['unidade_de_medida'].dropna().unique().tolist()
        print("INFO: Agente Classificador baseado em LLM inicializado com sucesso.")

    def _build_prompt(self, query: str):
        prompt = f"""
        Você é um engenheiro de orçamentos especialista em classificar serviços de construção civil. Sua tarefa é analisar a solicitação do usuário e retornar a classificação mais provável para o 'Grupo de Serviço' e a 'Unidade de Medida'.

        Solicitação do Usuário: "{query}"

        Responda APENAS com um formato JSON válido contendo as chaves "grupo" e "unidade". Escolha o grupo da lista de GRUPOS VÁLIDOS e a unidade da lista de UNIDADES VÁLIDAS.

        GRUPOS VÁLIDOS:
        {', '.join(self.grupos_unicos[:50])} 
        ... (e outros)

        UNIDADES VÁLIDAS:
        {', '.join(self.unidades_unicas)}

        JSON de Resposta:
        """
        return prompt

    def classify(self, query: str) -> tuple[str, str]:
        prompt = self._build_prompt(query)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            predicted_group = result.get("grupo", "N/A")
            predicted_unit = result.get("unidade", "N/A")
            
            print(f"DEBUG [Classificador LLM]: Query='{query}' -> Grupo='{predicted_group}', Unidade='{predicted_unit}'")
            return predicted_group, predicted_unit
        except Exception as e:
            print(f"ERRO [Classificador LLM]: {e}")
            return "N/A", "N/A"