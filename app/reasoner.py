# app/reasoner.py
import os
import re
from openai import OpenAI
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class ReasonerAgent:
    """
    Usa um LLM para analisar os resultados da busca e escolher a melhor resposta
    usando a técnica de Chain-of-Thought.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("A chave da API da OpenAI não foi encontrada. Verifique seu arquivo .env")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"

    def build_cot_prompt(self, user_query: str, search_results: list[dict]) -> str:
        """
        Constrói o prompt de Chain-of-Thought que guia o LLM a raciocinar.
        """
        prompt = "Você é um engenheiro orçamentista sênior e sua tarefa é escolher o serviço mais adequado de uma lista para atender a uma solicitação.\n"
        prompt += "Siga estritamente os seguintes passos:\n"
        prompt += "1. **Análise da Solicitação:** Analise a solicitação do usuário: \"" + user_query + "\". Identifique os principais componentes, materiais e ações descritas.\n"
        prompt += "2. **Avaliação dos Candidatos:** Avalie cada um dos serviços candidatos da lista abaixo, comparando-os com a sua análise da solicitação. Aponte os prós e contras de cada um.\n"
        prompt += "3. **Conclusão Final:** Com base na sua avaliação, declare qual é o serviço mais apropriado para a solicitação.\n"
        prompt += "4. **Resposta Final:** No final da sua resposta, inclua a linha 'CÓDIGO FINAL: [código_do_serviço_escolhido]'.\n\n"
        
        prompt += "--- SERVIÇOS CANDIDATOS ---\n"
        for item in search_results:
            prompt += f"- Código: {item['codigo']}, Descrição: {item['descricao']}\n"
        
        prompt += "\n--- INÍCIO DA ANÁLISE ---\n"
        return prompt

    def parse_response(self, response_text: str) -> str | None:
        """
        Extrai o código final da resposta do LLM usando uma expressão regular.
        """
        match = re.search(r"CÓDIGO FINAL:\s*(\d+)", response_text)
        if match:
            return match.group(1)
        
        # Fallback: se o padrão não for encontrado, tenta extrair qualquer número da última linha
        last_line = response_text.strip().split('\n')[-1]
        numbers = re.findall(r'\d+', last_line)
        if numbers:
            return numbers[-1]
            
        return None

    def choose_best_option(self, user_query: str, search_results: list[dict]) -> str | None:
        """
        Envia o prompt para a API da OpenAI e retorna o código escolhido.
        """
        if not search_results:
            return None
            
        prompt = self.build_cot_prompt(user_query, search_results)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500 # Aumentar os tokens para permitir o raciocínio
            )
            
            full_response = response.choices[0].message.content
            print(f"DEBUG: Resposta completa do LLM:\n---\n{full_response}\n---") # Log para depuração
            
            chosen_code = self.parse_response(full_response)
            return chosen_code
        except Exception as e:
            print(f"ERRO ao chamar a API do OpenAI: {e}")
            return None