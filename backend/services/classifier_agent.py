# /backend/services/classifier_agent.py
import pandas as pd
import os
import json
from openai import OpenAI

class ClassifierAgent:
    """
    Usa um LLM para realizar uma classificação de alta precisão.
    Carrega configurações dinamicamente do agents_config.json.
    """
    def __init__(self, data_filepath):
        self.client = OpenAI() # Reutiliza a chave do .env
        
        # Carrega configurações do agents_config.json
        self.model, self.base_prompt = self._load_config()

    
    def _load_config(self):
        """Carrega configurações do agents_config.json com fallback para valores padrão."""
        try:
            with open("agents_config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
                classifier_config = config.get('classifier_agent', {})
                model = classifier_config.get('model', 'gpt-4o-mini')
                base_prompt = classifier_config.get('base_prompt', 
                    'Você é um classificador especialista em serviços de construção civil. '
                    'Analise a query e retorne apenas o grupo e unidade mais prováveis baseados nos dados históricos. '
                    'Use JSON estrito como saída.')
                return model, base_prompt
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"AVISO: Erro ao carregar agents_config.json: {e}. Usando valores padrão.")
            return 'gpt-4o-mini', ('Você é um classificador especialista em serviços de construção civil. '
                                  'Analise a query e retorne apenas o grupo e unidade mais prováveis baseados nos dados históricos. '
                                  'Use JSON estrito como saída.')
        
        # Carrega os grupos e unidades ÚNICOS para dar como opções ao LLM
        df = pd.read_csv(data_filepath)
        self.grupos_unicos = df['descricao_do_grupo_de_servico'].dropna().unique().tolist()
        self.unidades_unicas = df['unidade_de_medida'].dropna().unique().tolist()
        print("INFO: Agente Classificador baseado em LLM inicializado com sucesso.")

    def _build_prompt(self, query: str):
        prompt = f"""
        {self.base_prompt}

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