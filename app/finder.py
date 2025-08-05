# app/finder.py
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import time
import os
from rank_bm25 import BM25Okapi
from app.text_utils import TextNormalizer

class ServicoFinder:
    def __init__(self, model_name=None):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"INFO: Usando dispositivo: {self.device}")
        
        # Usar modelo fine-tuned se disponível, senão usar o modelo base
        if model_name is None:
            fine_tuned_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'fine-tuned-construction-model-2025-08-04_00-01-43')
            if os.path.exists(fine_tuned_path):
                model_name = fine_tuned_path
                print(f"INFO: Usando modelo fine-tuned especializado: {model_name}")
            else:
                model_name = 'paraphrase-multilingual-mpnet-base-v2'
                print(f"INFO: Modelo fine-tuned não encontrado, usando modelo base: {model_name}")
        
        print(f"INFO: Carregando o modelo de Sentence Transformer...")
        self.model = SentenceTransformer(model_name, device=self.device)
        self.model_name = model_name
        self.dataframe = None
        self.corpus_embeddings = None
        self.bm25_index = None
        self.tokenized_corpus = None
        self.normalizer = TextNormalizer()
        print("INFO: Modelo carregado com sucesso.")
    
    def _convert_price_to_float(self, price_value):
        """Converte valores monetários brasileiros para float"""
        if price_value in [None, 'N/A', '', 0]:
            return 0.0
        
        try:
            # Se já é um número, retorna como float
            if isinstance(price_value, (int, float)):
                return float(price_value)
            
            # Se é string, trata formato brasileiro (vírgula como decimal)
            price_str = str(price_value).strip()
            if not price_str:
                return 0.0
            
            # Remove espaços e caracteres não numéricos exceto vírgula e ponto
            price_str = ''.join(c for c in price_str if c.isdigit() or c in '.,').strip()
            
            # Se tem vírgula, assume formato brasileiro (vírgula = decimal)
            if ',' in price_str:
                # Se tem ponto e vírgula, ponto é separador de milhares
                if '.' in price_str and ',' in price_str:
                    price_str = price_str.replace('.', '').replace(',', '.')
                else:
                    # Só vírgula, substitui por ponto
                    price_str = price_str.replace(',', '.')
            
            return float(price_str)
            
        except (ValueError, TypeError):
            print(f"AVISO: Não foi possível converter preço '{price_value}' para float, usando 0.0")
            return 0.0

    def load_and_index_services(self, filepath=None, force_reindex=False):
        """Carrega a base de conhecimento pré-processada"""
        if filepath is None:
            # Tenta carregar a base corrigida primeiro, depois otimizada, senão usa a padrão
            fixed_path = 'dados/knowledge_base_fixed.csv'
            optimized_path = 'dados/knowledge_base_optimized.csv'
            standard_path = 'dados/knowledge_base.csv'
            
            if os.path.exists(fixed_path):
                print("🎯 Usando base de conhecimento corrigida com dados SINAPI-CT")
                filepath = fixed_path
            elif os.path.exists(optimized_path):
                print("🎯 Usando base de conhecimento otimizada")
                filepath = optimized_path
            elif os.path.exists(standard_path):
                print("📋 Usando base de conhecimento padrão")
                filepath = standard_path
            else:
                raise FileNotFoundError("Nenhuma base de conhecimento encontrada")
        
        print(f"INFO: Carregando base de conhecimento: {filepath}")
        
        # Carrega o CSV da base de conhecimento
        self.dataframe = pd.read_csv(filepath, encoding='utf-8', quoting=1)
        # Reset do índice para garantir que os índices sejam sequenciais
        self.dataframe = self.dataframe.reset_index(drop=True)
        print(f"INFO: Base carregada: {len(self.dataframe)} registros")
        
        # Usa a coluna 'descricao_normalizada' para criar os índices
        corpus = self.dataframe['descricao_normalizada'].tolist()
        
        # Cache baseado no nome do arquivo
        cache_dir = os.path.join(os.path.dirname(filepath), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        # Nome do modelo para cache
        if os.path.isdir(self.model_name):
            model_safe_name = os.path.basename(self.model_name)
        else:
            model_safe_name = self.model_name.replace('/', '_').replace('-', '_')
        
        model_safe_name = model_safe_name.replace(':', '_').replace('\\', '_')
        cache_path_embeddings = os.path.join(cache_dir, f'kb_embeddings_{model_safe_name}.pt')
        
        # Verifica cache
        if not force_reindex and os.path.exists(cache_path_embeddings):
            print("INFO: Carregando embeddings do cache...")
            self.corpus_embeddings = torch.load(cache_path_embeddings, map_location=self.device)
        else:
            print(f"INFO: Gerando embeddings semânticos...")
            self.corpus_embeddings = self.model.encode(corpus, convert_to_tensor=True, show_progress_bar=True, device=self.device)
            torch.save(self.corpus_embeddings, cache_path_embeddings)
            print("INFO: Embeddings salvos no cache.")
        
        # Cria índice BM25 (sempre recriado)
        print(f"INFO: Criando índice BM25...")
        self.tokenized_corpus = [doc.lower().split(" ") for doc in corpus]
        self.bm25_index = BM25Okapi(self.tokenized_corpus)
        
        print("INFO: Indexação concluída.")

    def find_similar_semantic(self, query: str, top_k: int):
        """Busca semântica usando embeddings"""
        normalized_query = self.normalizer.normalize(query)
        query_embedding = self.model.encode(normalized_query, convert_to_tensor=True, device=self.device)
        cos_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        top_results = torch.topk(cos_scores, k=min(top_k, len(self.dataframe)))
        
        return top_results.indices.cpu().numpy(), top_results.values.cpu().numpy()

    def find_similar_keyword(self, query: str, top_k: int):
        """Busca por palavra-chave usando BM25"""
        normalized_query = self.normalizer.normalize(query)
        tokenized_query = normalized_query.split(" ")
        doc_scores = self.bm25_index.get_scores(tokenized_query)
        
        top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        top_scores = [doc_scores[i] for i in top_indices]
        
        return top_indices, top_scores

    def hybrid_search(self, query: str, top_k: int = 5, alpha: float = 0.5, 
                      predicted_group: str = None, predicted_unit: str = None, 
                      group_boost: float = 1.5, unit_boost: float = 1.2):
        """Executa busca híbrida combinando semântica e palavra-chave"""
        try:
            if self.corpus_embeddings is None or self.bm25_index is None:
                raise RuntimeError("ERRO: Os serviços não foram carregados. Execute 'load_and_index_services' primeiro.")

            print(f"DEBUG: Iniciando busca híbrida para: '{query}'")
            
            # Busca semântica
            semantic_indices, semantic_scores = self.find_similar_semantic(query, top_k=100)
            
            # Busca por palavra-chave
            keyword_indices, keyword_scores = self.find_similar_keyword(query, top_k=100)

            # Mapeia índice para score semântico
            semantic_score_map = {idx: score for idx, score in zip(semantic_indices, semantic_scores)}

            # Combina scores usando Reciprocal Rank Fusion
            fused_scores = {}
            
            # Peso da busca semântica
            for rank, (idx, score) in enumerate(zip(semantic_indices, semantic_scores)):
                if idx not in fused_scores:
                    fused_scores[idx] = 0
                fused_scores[idx] += alpha * (1 / (rank + 60))

            # Peso da busca por palavra-chave
            for rank, (idx, score) in enumerate(zip(keyword_indices, keyword_scores)):
                if idx not in fused_scores:
                    fused_scores[idx] = 0
                fused_scores[idx] += (1 - alpha) * (1 / (rank + 60))
            
            # Re-ranquear
            reranked_indices = sorted(fused_scores.keys(), key=lambda idx: fused_scores[idx], reverse=True)
            
            # Score semântico do melhor resultado
            top_semantic_score = 0.0
            if reranked_indices:
                top_item_index = reranked_indices[0]
                top_semantic_score = float(semantic_score_map.get(top_item_index, 0.0))
            
            # Monta resultado final
            results = []
            for idx in reranked_indices[:top_k]:
                # Verificação de segurança para evitar índices fora dos limites
                if idx >= len(self.dataframe):
                    print(f"AVISO: Índice {idx} fora dos limites (tamanho: {len(self.dataframe)})")
                    continue
                item = self.dataframe.iloc[idx]
                results.append({
                    'rank': len(results) + 1,
                    'score': float(f"{fused_scores[idx]:.4f}"),
                    'semantic_score': float(semantic_score_map.get(idx, 0.0)),
                    'codigo': str(item.get('codigo', 'N/A')),
                    'descricao': str(item.get('descricao', 'N/A')),
                    'preco': self._convert_price_to_float(item.get('preco', 0)),
                    'unidade': str(item.get('unidade', 'N/A')),
                    'fonte': str(item.get('fonte', 'N/A'))
                })
            
            print(f"DEBUG: Retornando {len(results)} resultados finais")
            return results, top_semantic_score
            
        except Exception as e:
            print(f"ERRO na busca híbrida: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    def find_similar(self, query: str, top_k: int = 5):
        """Método de compatibilidade - usa busca híbrida"""
        results, _ = self.hybrid_search(query, top_k)
        return results