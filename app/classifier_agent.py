# /app/classifier_agent.py
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
import joblib
import os

class ClassifierAgent:
    """
    Usa Machine Learning para classificar uma query de texto em
    'Grupo de Serviço' e 'Unidade de Medida'.
    """
    def __init__(self, data_filepath):
        self.model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'classifier_pipeline.joblib')
        
        # Se for a base de conhecimento, usar o arquivo original para treinamento
        if 'knowledge_base.csv' in data_filepath:
            original_filepath = os.path.join(os.path.dirname(data_filepath), 'banco_dados_servicos.txt')
            if os.path.exists(original_filepath):
                self.df = pd.read_csv(original_filepath)
            else:
                self.df = pd.read_csv(data_filepath)
        else:
            self.df = pd.read_csv(data_filepath)
        
        # Limpeza básica e preparação dos dados
        self.df.rename(columns={
            'descricao_completa_do_servico_prestado': 'descricao',
            'descricao_do_grupo_de_servico': 'grupo',
            'unidade_de_medida': 'unidade'
        }, inplace=True)
        
        # Verifica se as colunas existem antes de fazer dropna
        required_cols = ['descricao']
        if 'grupo' in self.df.columns:
            required_cols.append('grupo')
        if 'unidade' in self.df.columns:
            required_cols.append('unidade')
            
        self.df.dropna(subset=required_cols, inplace=True)

        if os.path.exists(self.model_path):
            print("INFO: Carregando modelo de classificação pré-treinado...")
            self.pipeline = joblib.load(self.model_path)
        else:
            print("INFO: Modelo de classificação não encontrado. Treinando um novo modelo...")
            self.pipeline = self._train()
            joblib.dump(self.pipeline, self.model_path)
            print(f"INFO: Modelo de classificação salvo em {self.model_path}")

    def _train(self):
        """
        Treina um pipeline de classificação.
        """
        # Features (X) e Targets (y)
        X = self.df['descricao']
        # Nosso modelo vai prever uma string combinada "grupo;unidade"
        y = self.df['grupo'] + ";" + self.df['unidade']

        # Criação do Pipeline de Machine Learning
        # 1. TF-IDF Vectorizer: Transforma texto em vetores numéricos
        # 2. LinearSVC: Um classificador rápido e eficiente para texto
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_df=0.9, min_df=5)),
            ('clf', LinearSVC(C=1.0, class_weight='balanced', random_state=42))
        ])
        
        print("INFO: Treinamento do pipeline de classificação em andamento...")
        pipeline.fit(X, y)
        print("INFO: Treinamento concluído.")
        return pipeline

    def classify(self, query: str) -> (str, str):
        """
        Prevê o grupo e a unidade para uma nova query.
        """
        prediction = self.pipeline.predict([query])[0]
        predicted_group, predicted_unit = prediction.split(";")
        
        print(f"DEBUG [Classificador]: Query='{query}' -> Grupo='{predicted_group}', Unidade='{predicted_unit}'")
        return predicted_group, predicted_unit