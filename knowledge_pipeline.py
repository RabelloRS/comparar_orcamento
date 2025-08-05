# knowledge_pipeline.py
import pandas as pd
import os
import fitz  # PyMuPDF
import re
from collections import Counter
from unidecode import unidecode
from app.text_utils import TextNormalizer # Reutilizamos nosso normalizador

class KnowledgePipeline:
    def __init__(self):
        self.docs_path = 'documentos'
        self.data_path = 'dados'
        self.main_db_path = os.path.join(self.data_path, 'banco_dados_servicos.txt')
        self.output_kb_path = os.path.join(self.data_path, 'knowledge_base.csv')
        self.normalizer = TextNormalizer()
        print("INFO: Pipeline de Conhecimento inicializado.")

    def _extract_text_from_pdf(self, file_path):
        """Extrai texto de um arquivo PDF."""
        try:
            doc = fitz.open(file_path)
            text = " ".join(page.get_text("text") for page in doc)
            return self.normalizer.normalize(text)
        except Exception as e:
            print(f"AVISO: Não foi possível ler o PDF '{os.path.basename(file_path)}': {e}")
            return ""

    def run(self):
        print("\n--- INICIANDO EXECUÇÃO DO PIPELINE DE CONHECIMENTO ---")

        # 1. Carregar a base de dados principal
        print("ETAPA 1: Carregando banco de dados principal...")
        if not os.path.exists(self.main_db_path):
            print(f"ERRO: Banco de dados principal não encontrado em '{self.main_db_path}'")
            return
        df_db = pd.read_csv(self.main_db_path)
        df_db.rename(columns={
            'codigo_da_composicao': 'codigo', 'descricao_completa_do_servico_prestado': 'descricao_original',
            'unidade_de_medida': 'unidade', 'orgao_responsavel_pela_divulgacao': 'fonte',
            'descricao_do_grupo_de_servico': 'grupo', 'precos_unitarios_dos_servicos': 'preco'
        }, inplace=True)
        df_db['codigo'] = df_db['codigo'].astype(str)

        # 2. Gerar Termos-Chave por Grupo de Serviço
        print("ETAPA 2: Gerando termos-chave por grupo de serviço...")
        df_db['grupo'] = df_db['grupo'].astype(str)
        group_keywords = {}
        for group_name, group_df in df_db.groupby('grupo'):
            # Pega as 100 palavras mais comuns do grupo, ignorando palavras muito curtas
            all_text = " ".join(group_df['descricao_original'].apply(self.normalizer.normalize))
            words = [word for word in all_text.split() if len(word) > 3]
            group_keywords[group_name] = [word for word, _ in Counter(words).most_common(100)]
        print(f"INFO: {len(group_keywords)} grupos de serviço analisados.")

        # 3. Processar todos os PDFs e associar o texto
        print("ETAPA 3: Processando PDFs e associando conhecimento...")
        if not os.path.exists(self.docs_path):
            print(f"AVISO: Pasta de documentos '{self.docs_path}' não encontrada. Continuando sem enriquecimento de PDFs.")
            doc_associations = {}
        else:
            pdf_files = [f for f in os.listdir(self.docs_path) if f.lower().endswith('.pdf')]
            print(f"INFO: Encontrados {len(pdf_files)} arquivos PDF para processar.")
            
            doc_associations = {}
            for i, filename in enumerate(pdf_files[:10]):  # Limita a 10 PDFs para evitar problemas de memória
                print(f"  Processando PDF {i+1}/10: {filename}")
                text = self._extract_text_from_pdf(os.path.join(self.docs_path, filename))
                if not text: continue
                
                # Processa apenas os primeiros 5000 caracteres para economizar memória
                text = text[:5000]
                
                for group_name, keywords in group_keywords.items():
                    # Conta quantos termos-chave do grupo aparecem no PDF
                    match_count = sum(1 for keyword in keywords[:20] if keyword in text)  # Usa apenas os 20 termos mais importantes
                    # Heurística: se mais de 3 termos-chave do grupo estão no PDF, cria uma associação
                    if match_count >= 3:
                        print(f"    -> Associação encontrada: Grupo '{group_name}' <-> Documento '{filename}' ({match_count} termos)")
                        if group_name not in doc_associations:
                            doc_associations[group_name] = ""
                        doc_associations[group_name] += text[:1000] + " "  # Adiciona apenas os primeiros 1000 caracteres

        # 4. Construir a Base de Conhecimento Final
        print("ETAPA 4: Construindo a Base de Conhecimento Final...")
        
        def get_associated_text(group):
            return doc_associations.get(group, "")

        df_db['texto_enriquecido_docs'] = df_db['grupo'].apply(get_associated_text)
        
        # Cria a descrição final para a IA
        df_db.fillna('', inplace=True)
        df_db['descricao_para_ia'] = df_db['descricao_original'] + " | " + df_db['texto_enriquecido_docs']
        df_db['descricao_normalizada'] = df_db['descricao_para_ia'].apply(self.normalizer.normalize)

        # Seleciona e salva as colunas finais
        final_columns = ['codigo', 'descricao_original', 'unidade', 'preco', 'fonte', 'grupo', 'descricao_normalizada']
        df_final = df_db[final_columns]
        
        df_final.to_csv(self.output_kb_path, index=False, encoding='utf-8-sig', quoting=1)  # quoting=1 para escapar caracteres especiais
        print(f"\n✅ SUCESSO! Base de conhecimento final e robusta criada em '{self.output_kb_path}' com {len(df_final)} registros.")

if __name__ == "__main__":
    pipeline = KnowledgePipeline()
    pipeline.run()