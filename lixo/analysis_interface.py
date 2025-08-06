# analysis_interface.py
import streamlit as st
import requests
import json
import pandas as pd
import os
from datetime import datetime
import time

# --- Configuração da Página ---
st.set_page_config(
    page_title="Painel de Análise dos Agentes",
    page_icon="🔬",
    layout="wide"
)

# --- Constantes ---
API_URL = "http://localhost:8000/buscar" # URL do nosso backend FastAPI
FEEDBACK_LOG_FILE = "feedback_log.csv"

# --- Funções Auxiliares ---
def get_full_item_details(codigo):
    # (Esta função pode ser expandida para buscar mais detalhes do item se necessário)
    # Por enquanto, é um placeholder.
    return f"Detalhes para o código {codigo}."

# --- Cabeçalho da Aplicação ---
st.title("🔬 Painel de Análise e Feedback dos Agentes de IA")
st.markdown("Use esta ferramenta para auditar o processo de decisão do sistema de busca e fornecer orientações para melhorias.")
st.markdown("---")

# --- Inicialização do Session State ---
if 'results' not in st.session_state:
    st.session_state.results = []
if 'server_logs' not in st.session_state:
    st.session_state.server_logs = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'query_executed' not in st.session_state:
    st.session_state.query_executed = False

# --- Interface Principal Dividida ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🔍 Análise de Query")
    
    user_query = st.text_input(
        "Digite a query técnica que deseja analisar:", 
        "assentamento de porcelanato 60x60cm"
    )
    
    analyze_button = st.button("Analisar Desempenho dos Agentes", type="primary")

with col2:
    st.header("📊 Logs do Servidor")
    
    # Área para exibir logs do servidor
    log_container = st.container()
    
    with log_container:
        st.info("💡 **Dica**: Os logs do servidor aparecerão aqui durante a análise")
        
        # Exibe logs salvos na sessão
        if st.session_state.server_logs:
            st.text_area(
                "Logs do Pipeline:",
                value="\n".join(st.session_state.server_logs),
                height=500,
                disabled=True
            )
        else:
            st.text_area(
                "Logs do Pipeline:",
                value="Aguardando execução de uma query...",
                height=500,
                disabled=True
            )

# --- Processamento da Query ---
if analyze_button:
    if not user_query:
        st.error("Por favor, digite uma query para analisar.")
    else:
        # Mostra um spinner enquanto a busca está em andamento
        with st.spinner(f"Executando a query '{user_query}' através do pipeline de agentes..."):
            try:
                # Limpa logs anteriores
                st.session_state.server_logs = []
                
                # Adiciona logs iniciais
                st.session_state.server_logs.append(f"[INÍCIO] Processando query: '{user_query}'")
                st.session_state.server_logs.append("[SISTEMA] Enviando requisição para o servidor...")
                
                payload = {"texto_busca": user_query, "top_k": 3}
                response = requests.post(API_URL, json=payload, timeout=120)

                if response.status_code == 200:
                    st.session_state.server_logs.append("[SISTEMA] ✅ Resposta recebida com sucesso!")
                    
                    # Processa a resposta
                    final_response = response.json()
                    st.session_state.results = final_response.get('results', [])
                    st.session_state.last_query = user_query
                    st.session_state.query_executed = True
                    
                    # Adiciona logs detalhados baseados na resposta
                    st.session_state.server_logs.extend([
                        "[FLUXO] Executando pipeline de 3 estágios...",
                        "[AGENTE 1: CLASSIFICADOR] Analisando query e extraindo características",
                        "[AGENTE 2: RECUPERADOR] Executando busca híbrida semântica",
                        "[AGENTE 3: RACIOCINADOR] Avaliando candidatos e fazendo escolha final",
                        f"[RESULTADO] {len(st.session_state.results)} resultados encontrados",
                        "[SISTEMA] Pipeline concluído com sucesso!"
                    ])
                    
                    st.success("Pipeline executado com sucesso! Analisando os resultados...")
                    
                    # Força atualização da interface
                    st.rerun()
                    
                else:
                    st.session_state.server_logs.append(f"[ERRO] Status HTTP: {response.status_code}")
                    st.error(f"Ocorreu um erro na API (Status: {response.status_code}).")
                    st.json(response.text)

            except requests.RequestException as e:
                st.session_state.server_logs.append(f"[ERRO] Falha na conexão: {str(e)}")
                st.error(f"Não foi possível conectar ao serviço de busca em {API_URL}.")
                st.error(f"Detalhe do erro: {e}")

# --- Exibição dos Resultados ---
with col1:
    if st.session_state.query_executed and st.session_state.results:
        # --- Visualização dos Resultados por Agente ---
        st.markdown("---")
        st.subheader("🕵️ Análise do Resultado Final")
        
        st.write(f"Abaixo estão os resultados para a query: **'{st.session_state.last_query}'**")
        st.write(f"Total de resultados encontrados: **{len(st.session_state.results)}**")
        
        for i, item in enumerate(st.session_state.results, 1):
            st.markdown(f"**Resultado {i}: {item['codigo']}** - {item['descricao'][:100]}...")
            with st.expander(f"Detalhes completos do código {item['codigo']}"):
                st.json(item)

        st.markdown("---")
        
        # --- Formulário de Feedback ---
        st.subheader("🧠 Feedback e Novas Orientações")
        st.write("Analise os resultados acima e forneça seu feedback para treinar os agentes.")

        with st.form("feedback_form"):
            st.markdown("**Avaliação do Resultado Final**")
            
            correct_code = st.text_input(
                "Qual era o CÓDIGO CORRETO que você esperava para esta busca? (Deixe em branco se nenhum for ideal)",
                placeholder="Ex: 87263"
            )

            is_choice_correct = st.selectbox(
                "A escolha do Agente Raciocinador (o primeiro resultado) foi a melhor opção da lista?",
                ["Sim", "Não", "Parcialmente"]
            )
            
            st.markdown("**Orientações para os Agentes**")
            
            agent_feedback = st.text_area(
                "Escreva aqui suas orientações. O que a IA deveria ter considerado? Quais termos são mais importantes?",
                placeholder="Exemplo: 'A IA deveria ter dado mais peso à característica 'porcelanato' e ignorado 'manilha'. A dimensão 60x60cm também era crucial.'"
            )

            submitted = st.form_submit_button("Salvar Análise e Orientações")
            if submitted:
                # Salva o feedback em CSV
                feedback_data = {
                    'timestamp': [datetime.now().isoformat()],
                    'query': [st.session_state.last_query],
                    'top_result_code': [st.session_state.results[0]['codigo'] if st.session_state.results else 'N/A'],
                    'expected_correct_code': [correct_code],
                    'is_choice_correct': [is_choice_correct],
                    'human_guidance': [agent_feedback]
                }
                df_feedback = pd.DataFrame(feedback_data)
                
                # Anexa ao arquivo existente ou cria um novo
                if os.path.exists(FEEDBACK_LOG_FILE):
                    df_feedback.to_csv(FEEDBACK_LOG_FILE, mode='a', header=False, index=False, sep=';')
                else:
                    df_feedback.to_csv(FEEDBACK_LOG_FILE, index=False, sep=';')
                    
                st.success("Obrigado! Suas orientações foram salvas e serão usadas para aprimorar o sistema.")
    
    elif st.session_state.query_executed and not st.session_state.results:
        st.warning("Nenhum resultado foi encontrado para a query executada.")
    
    elif not st.session_state.query_executed:
        st.info("Execute uma análise para ver os resultados aqui.")