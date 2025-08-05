# /app/text_utils.py
import re
import unicodedata

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