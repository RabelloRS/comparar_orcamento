# /core/text_utils.py
import re
import unicodedata
from openai import OpenAI

class TextNormalizer:
    def __init__(self):
        self.substitutions = {
            r'\b(m2|m²)\b': ' metro_quadrado ', r'\b(m3|m³)\b': ' metro_cubico ',
            r'\b(pol|polegadas|")\b': ' polegada ', r'\b(ø)\b': ' diametro ',
            r'\b(conc)\b': 'concreto', r'\b(arm)\b': 'armado', r'\b(est)\b': 'estrutural',
            r'\b(galv)\b': 'galvanizado', r'\b(exec)\b': 'execucao',
            r'\b(fornec)\b': 'fornecimento', r'\b(inst)\b': 'instalacao',
            r'\b(diam)\b': 'diametro', r'\bfck\b': 'fck', r'\b(mpa)\b': 'mpa',
            r'\b(kv)\b': 'kv', r'\b(mm2|mm²)\b': 'mm2', r'\b(btu)\b': 'btu'
        }

    def normalize(self, text: str) -> str:
        if not isinstance(text, str): return ''
        text = text.lower()
        text = str(unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8', 'ignore'))

        for pattern, replacement in self.substitutions.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            
        # Remove caracteres especiais mas PRESERVA números, pontos e vírgulas (para decimais)
        text = re.sub(r'[^a-z0-9_., ]', ' ', text)
        text = ' '.join(text.split())
        return text


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
        return query  # Retorna a query original em caso de erro


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