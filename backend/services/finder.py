# /app/finder.py
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import os
from rank_bm25 import BM25Okapi
from backend.core.text_utils import TextNormalizer # Importa nosso normalizador validado
import pickle # Biblioteca para salvar/carregar objetos Python

class ServicoFinder:
    """
    Versão final e otimizada do Recuperador.
    Inclui um sistema de cache robusto para uma inicialização quase instantânea.
    """
    def __init__(self, model_name='paraphrase-multilingual-mpnet-base-v2'):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = SentenceTransformer(model_name, device=self.device)
        self.normalizer = TextNormalizer()
        self.dataframe = None
        self.corpus_embeddings = None
        self.bm25_index = None
        print("INFO: ServicoFinder (versão com cache) inicializado.")

    def _convert_price_to_float(self, price_value):
        """
        Converte um valor de preço (que pode ser string com vírgula) para float.
        Retorna 0.0 se a conversão falhar.
        """
        if isinstance(price_value, (int, float)):
            return float(price_value)
        if isinstance(price_value, str):
            try:
                # Substitui a vírgula por ponto e converte para float
                return float(price_value.replace('.', '').replace(',', '.'))
            except (ValueError, AttributeError):
                return 0.0
        return 0.0

    def _preprocess_data(self, filepath):
        """
        Lê e pré-processa o banco de dados principal de serviços.
        """
        print(f"INFO: Processando arquivo de dados principal: {filepath}")
        df = pd.read_csv(filepath, dtype={'codigo_da_composicao': str})
        
        # Renomeia para nosso padrão interno, garantindo que todas as colunas sejam lidas
        df.rename(columns={
            'codigo_da_composicao': 'codigo', 
            'descricao_completa_do_servico_prestado': 'descricao_original',
            'unidade_de_medida': 'unidade', 
            'orgao_responsavel_pela_divulgacao': 'fonte',
            'descricao_do_grupo_de_servico': 'grupo', 
            'precos_unitarios_dos_servicos': 'preco'
        }, inplace=True, errors='ignore')

        # Garante que as colunas essenciais existam
        essential_cols = ['codigo', 'descricao_original', 'unidade', 'preco', 'fonte', 'grupo']
        for col in essential_cols:
            if col not in df.columns:
                raise ValueError(f"ERRO CRÍTICO: A coluna essencial '{col}' não foi encontrada em '{filepath}'.")

        df.fillna('', inplace=True)
        
        # Aplica a normalização avançada na descrição original
        print("INFO: Aplicando normalização de texto avançada...")
        df['descricao_normalizada'] = df['descricao_original'].apply(self.normalizer.normalize)
        
        # A coluna 'descricao' que será usada para a indexação será a normalizada
        df['descricao'] = df['descricao_normalizada']
        
        print(f"INFO: Pré-processamento concluído. {len(df)} registros carregados e normalizados.")
        return df

    def load_and_index_services(self, data_filepath, force_reindex=False):
        """
        Carrega os dados e índices. Se um cache válido existir, carrega dele.
        Caso contrário, processa os dados e cria o cache para futuras execuções.
        """
        cache_dir = os.path.join('dados', 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        # Define os caminhos para os arquivos de cache
        df_cache_path = os.path.join(cache_dir, 'dataframe.pkl')
        bm25_cache_path = os.path.join(cache_dir, 'bm25_index.pkl')
        embeddings_cache_path = os.path.join(cache_dir, 'embeddings.pt')

        # --- LÓGICA DE CARREGAMENTO DO CACHE ---
        if not force_reindex and all(os.path.exists(p) for p in [df_cache_path, bm25_cache_path, embeddings_cache_path]):
            print("\nINFO: Cache válido encontrado! Carregando índices pré-processados...")
            
            self.dataframe = pd.read_pickle(df_cache_path)
            with open(bm25_cache_path, 'rb') as f:
                self.bm25_index = pickle.load(f)
            self.corpus_embeddings = torch.load(embeddings_cache_path, map_location=self.device)
            
            print("SUCESSO: Índices carregados do cache. Inicialização rápida concluída.")
            return

        # --- LÓGICA DE PROCESSAMENTO (se não houver cache) ---
        print("\nAVISO: Cache não encontrado ou 'force_reindex' ativado. Iniciando processamento completo...")
        
        self.dataframe = self._preprocess_data(data_filepath)
        
        corpus = self.dataframe['descricao'].tolist()
        
        print("INFO: Criando índice de palavra-chave (BM25)...")
        tokenized_corpus = [doc.split(" ") for doc in corpus]
        self.bm25_index = BM25Okapi(tokenized_corpus)
        
        print("INFO: Gerando embeddings semânticos... (Isso pode demorar)")
        self.corpus_embeddings = self.model.encode(corpus, convert_to_tensor=True, show_progress_bar=True, device=self.device)
        
        # 3. Salvar os novos índices no cache
        print("\nINFO: Salvando novos índices no cache para futuras inicializações...")
        self.dataframe.to_pickle(df_cache_path)
        with open(bm25_cache_path, 'wb') as f:
            pickle.dump(self.bm25_index, f)
        torch.save(self.corpus_embeddings, embeddings_cache_path)
        
        print("SUCESSO: Processamento concluído e cache criado.")

    # Os métodos de busca (`find_similar_semantic`, `find_similar_keyword`, `hybrid_search`)
    # permanecem exatamente os mesmos da versão anterior, pois já estão corretos e otimizados.
    # O agente deve garantir que eles estejam presentes no arquivo.
    def find_similar_semantic(self, query: str, top_k: int):
        normalized_query = self.normalizer.normalize(query)
        query_embedding = self.model.encode(normalized_query, convert_to_tensor=True, device=self.device)
        cos_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        top_results = torch.topk(cos_scores, k=min(top_k, len(self.dataframe)))
        return top_results.indices.cpu().numpy(), top_results.values.cpu().numpy()

    def find_similar_keyword(self, query: str, top_k: int):
        normalized_query = self.normalizer.normalize(query)
        tokenized_query = normalized_query.split(" ")
        doc_scores = self.bm25_index.get_scores(tokenized_query)
        top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        return top_indices

    def hybrid_search(self, query: str, top_k: int = 5, alpha: float = 0.5, 
                      predicted_group: str = None, predicted_unit: str = None, 
                      group_boost: float = 1.5, unit_boost: float = 1.2):
        
        # Inicializa o log detalhado do processo de raciocínio
        reasoning_log = []
        reasoning_log.append(f"🧠 **INÍCIO DO PROCESSO DE RACIOCÍNIO DA IA**")
        reasoning_log.append(f"📝 **Consulta recebida:** '{query}'")
        reasoning_log.append(f"⚙️ **Parâmetros:** top_k={top_k}, alpha={alpha}")
        
        if predicted_group or predicted_unit:
            reasoning_log.append(f"🎯 **Predições do classificador:**")
            if predicted_group:
                reasoning_log.append(f"   • Grupo previsto: {predicted_group} (boost: {group_boost}x)")
            if predicted_unit:
                reasoning_log.append(f"   • Unidade prevista: {predicted_unit} (boost: {unit_boost}x)")
        
        reasoning_log.append(f"\n🔍 **ETAPA 1: BUSCA SEMÂNTICA**")
        reasoning_log.append(f"   • Processando embeddings da consulta...")
        semantic_indices, semantic_scores = self.find_similar_semantic(query, top_k=100)
        reasoning_log.append(f"   • ✅ Encontrados {len(semantic_indices)} resultados semânticos")
        reasoning_log.append(f"   • 🏆 Melhor score semântico: {max(semantic_scores):.4f}")
        
        reasoning_log.append(f"\n🔤 **ETAPA 2: BUSCA POR PALAVRAS-CHAVE**")
        reasoning_log.append(f"   • Aplicando algoritmo BM25...")
        keyword_indices = self.find_similar_keyword(query, top_k=100)
        reasoning_log.append(f"   • ✅ Encontrados {len(keyword_indices)} resultados por palavras-chave")
        
        semantic_score_map = {idx: score for idx, score in zip(semantic_indices, semantic_scores)}
        
        reasoning_log.append(f"\n⚖️ **ETAPA 3: FUSÃO DE RESULTADOS**")
        reasoning_log.append(f"   • Combinando resultados semânticos (peso: {alpha:.1f}) e palavras-chave (peso: {1-alpha:.1f})")
        
        fused_scores = {}
        for rank, idx in enumerate(semantic_indices):
            fused_scores[idx] = fused_scores.get(idx, 0) + alpha * (1 / (rank + 60))
        for rank, idx in enumerate(keyword_indices):
            fused_scores[idx] = fused_scores.get(idx, 0) + (1 - alpha) * (1 / (rank + 60))
        
        reasoning_log.append(f"   • ✅ {len(fused_scores)} itens únicos após fusão")
        
        if predicted_group or predicted_unit:
            reasoning_log.append(f"\n🎯 **ETAPA 4: APLICAÇÃO DE BOOSTS INTELIGENTES**")
            boost_count = 0
            for idx in fused_scores:
                item_group = self.dataframe.iloc[idx].get('grupo', '')
                item_unit = self.dataframe.iloc[idx].get('unidade', '')
                original_score = fused_scores[idx]
                
                if predicted_group and item_group == predicted_group: 
                    fused_scores[idx] *= group_boost
                    boost_count += 1
                if predicted_unit and item_unit == predicted_unit: 
                    fused_scores[idx] *= unit_boost
                    boost_count += 1
                    
                if fused_scores[idx] != original_score:
                    reasoning_log.append(f"   • 🚀 Item {idx}: score {original_score:.4f} → {fused_scores[idx]:.4f}")
            
            reasoning_log.append(f"   • ✅ {boost_count} itens receberam boost de relevância")
        
        reasoning_log.append(f"\n📊 **ETAPA 5: RANKING FINAL**")
        reranked_indices = sorted(fused_scores.keys(), key=lambda idx: fused_scores[idx], reverse=True)
        reasoning_log.append(f"   • Ordenando {len(reranked_indices)} resultados por score final")
        
        # --- LÓGICA DE RETORNO ATUALIZADA ---
        top_original_index = -1
        top_semantic_score = 0.0
        if reranked_indices:
            top_item_index = reranked_indices[0]
            top_original_index = self.dataframe.iloc[top_item_index].name
            top_semantic_score = float(semantic_score_map.get(top_item_index, 0.0))
            
            reasoning_log.append(f"   • 🥇 Melhor resultado: índice {top_item_index} (score: {fused_scores[top_item_index]:.4f})")
        
        reasoning_log.append(f"\n🎯 **ETAPA 6: PREPARAÇÃO DOS RESULTADOS**")
        results = []
        for idx in reranked_indices[:top_k]:
            item = self.dataframe.iloc[idx]
            result_item = {
                'rank': len(results) + 1,
                'score': float(fused_scores[idx]),
                'codigo': item.get('codigo', 'N/A'),
                'descricao': item.get('descricao_original', 'N/A'),
                'preco': self._convert_price_to_float(item.get('preco')),
                'unidade': item.get('unidade', 'N/A'),
                'fonte': item.get('fonte', 'N/A')
            }
            results.append(result_item)
            
            reasoning_log.append(f"   • #{len(results)}: {item.get('codigo', 'N/A')} - Score: {fused_scores[idx]:.4f}")
        
        reasoning_log.append(f"\n✅ **PROCESSO CONCLUÍDO**")
        reasoning_log.append(f"   • {len(results)} resultados finais preparados")
        reasoning_log.append(f"   • Melhor score semântico: {top_semantic_score:.4f}")
        reasoning_log.append(f"   • Processo de raciocínio da IA finalizado com sucesso!")
        
        # Junta todo o log em uma string
        detailed_reasoning = "\n".join(reasoning_log)
        
        return results, top_semantic_score, top_original_index, detailed_reasoning