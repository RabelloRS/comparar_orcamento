# interface.py
import streamlit as st
import requests
import pandas as pd
import io
import os
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Assistente de Orçamento de Obras",
    page_icon="🏗️",
    layout="wide"
)

# --- Constantes e Cache ---
API_URL = "http://localhost:8000/buscar"
DATABASE_PATH = "dados/banco_dados_servicos.txt"
LOG_FILE = "processing_log.csv"
TEMP_DIR = "temp_files"

# Garante que o diretório de arquivos temporários exista
os.makedirs(TEMP_DIR, exist_ok=True)

@st.cache_data
def load_full_database():
    """Carrega o banco de dados completo de serviços em memória para a filtragem rápida."""
    try:
        df = pd.read_csv(DATABASE_PATH)
        df.rename(columns={'descricao_completa_do_servico_prestado': 'Descrição', 'codigo_da_composicao': 'Código'}, inplace=True)
        return df[['Código', 'Descrição']]
    except FileNotFoundError:
        st.error(f"Arquivo do banco de dados não encontrado em '{DATABASE_PATH}'. A filtragem em tempo real está desativada.")
        return pd.DataFrame(columns=['Código', 'Descrição'])

# Carrega os dados uma vez
full_db = load_full_database()

# --- Título da Aplicação ---
st.title("🏗️ Assistente de Orçamento de Obras Públicas")
st.markdown("Sistema inteligente para busca e análise de serviços de construção civil")

# --- Status da API ---
try:
    api_status = requests.get("http://localhost:8000/", timeout=2)
    if api_status.status_code == 200:
        st.success("🟢 API conectada e funcionando")
    else:
        st.warning("🟡 API respondendo com problemas")
except requests.exceptions.RequestException:
    st.error("🔴 API desconectada")
    with st.expander("ℹ️ Como iniciar o backend"):
        st.code("""
# No terminal, execute:
cd app
python -m uvicorn main:app --reload --port 8000
        """)

st.markdown("---")

# --- Divisão da Tela em Duas Colunas ---
col1, col2 = st.columns(2, gap="large")

# --- PAINEL 1: BUSCA SEMÂNTICA INTELIGENTE ---
with col1:
    st.header("1. Busca Semântica (IA)")
    st.info("Use esta busca para encontrar serviços por contexto, sinônimos ou descrições incompletas.")

    # Input do usuário para busca semântica
    semantic_query = st.text_input(
        "Descreva o serviço ou insumo desejado:", 
        "concreto para fundação",
        key="semantic_search"
    )
    top_k = st.slider("Número de resultados a exibir:", min_value=1, max_value=10, value=3, key="top_k_slider")

    if st.button("Buscar com IA", type="primary"):
        if not semantic_query:
            st.error("Por favor, digite uma descrição para a busca.")
        else:
            with st.spinner(f"Analisando '{semantic_query}' com a equipe de agentes..."):
                try:
                    payload = {"texto_busca": semantic_query, "top_k": top_k}
                    response = requests.post(API_URL, json=payload, timeout=60)
                    
                    if response.status_code == 200:
                        results = response.json().get('results', [])
                        if not results:
                            st.warning("Nenhum resultado encontrado.")
                        else:
                            st.success(f"Encontrados {len(results)} resultados relevantes:")
                            for item in results:
                                # Tratamento mais seguro da descrição
                                descricao_curta = item.get('descricao', 'N/A')
                                if '|' in descricao_curta:
                                    descricao_curta = descricao_curta.split('|')[0].strip()
                                
                                with st.expander(f"**{item.get('codigo', 'N/A')}** - {descricao_curta}"):
                                    st.markdown(f"**Descrição Completa:** {item.get('descricao', 'N/A')}")
                                    st.markdown("---")
                                    c1, c2, c3, c4 = st.columns(4)
                                    c1.metric("Preço Unitário", f"R$ {item.get('preco', 0.0):.2f}")
                                    c2.metric("Unidade", item.get('unidade', 'N/A'))
                                    c3.metric("Fonte", item.get('fonte', 'N/A'))
                                    c4.metric("Confiança", f"{item.get('score', 0.0):.4f}")
                    
                    elif response.status_code == 422:
                        st.error("Erro de validação: Verifique se os parâmetros estão corretos.")
                    elif response.status_code == 500:
                        st.error("Erro interno do servidor. Tente novamente em alguns instantes.")
                    else:
                        st.error(f"Erro na API (Status: {response.status_code}): {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Não foi possível conectar ao serviço de busca em {API_URL}.")
                    st.info("💡 **Para usar a busca semântica:**\n1. Abra um terminal\n2. Execute: `cd app && python -m uvicorn main:app --reload --port 8000`\n3. Aguarde a mensagem 'Aplicação pronta para receber requisições'")
                except requests.exceptions.Timeout:
                    st.error("⏱️ Timeout: A busca demorou mais que o esperado. Tente novamente.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Erro de conexão: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Erro inesperado: {str(e)}")

# --- PAINEL 2: FILTRAGEM INSTANTÂNEA ---
with col2:
    st.header("2. Filtro Rápido em Tempo Real")
    st.info("Digite qualquer parte do nome do serviço para filtrar a lista completa instantaneamente.")

    # Input do usuário para filtragem
    filter_query = st.text_input(
        "Digite para filtrar...",
        "",
        key="filter_search",
        placeholder="Ex: alvenaria bloco ceramico"
    )

    if filter_query:
        # Filtra o DataFrame em tempo real
        # A flag `case=False` ignora maiúsculas/minúsculas. `na=False` trata células vazias.
        filtered_df = full_db[full_db['Descrição'].str.contains(filter_query, case=False, na=False)]
        st.dataframe(filtered_df, use_container_width=True, height=350)
    else:
        st.write("A lista completa de serviços aparecerá aqui assim que você começar a digitar.")
        st.dataframe(full_db.head(10), use_container_width=True, height=350) # Mostra os 10 primeiros por padrão

# --- SEÇÃO 3: PROCESSAMENTO DE PLANILHAS EM LOTE (VERSÃO RESILIENTE) ---
st.markdown("\n---\n")
st.header("📋 Processamento de Planilhas em Lote (com Salvamento Automático)")
st.info("Faça o upload de uma planilha Excel (.xlsx) com a coluna 'descricao'. O sistema processará linha por linha, salvando o progresso continuamente.")

uploaded_file = st.file_uploader("Escolha uma planilha Excel", type=["xlsx"])

if uploaded_file is not None:
    df_upload = pd.read_excel(uploaded_file)
    st.write("Pré-visualização da sua planilha:")
    st.dataframe(df_upload.head())

    if 'descricao' not in df_upload.columns:
        st.error("A planilha precisa ter uma coluna chamada 'descricao'. Por favor, ajuste e tente novamente.")
    else:
        if st.button("Iniciar Processamento Resiliente", type="primary"):
            # Adiciona as novas colunas se não existirem
            for col in ['codigo_encontrado', 'fonte_encontrada', 'descricao_encontrada', 'unidade_encontrada', 'valor_unitario_encontrado']:
                if col not in df_upload.columns:
                    df_upload[col] = ''
            
            # Gera nomes de arquivo únicos para esta sessão de processamento
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_excel_path = os.path.join(TEMP_DIR, f"processado_{timestamp}.xlsx")
            log_path = os.path.join(TEMP_DIR, f"log_{timestamp}.csv")
            
            st.warning(f"O progresso será salvo continuamente no arquivo: '{temp_excel_path}'")
            
            progress_bar = st.progress(0, text="Iniciando processamento...")
            total_rows = len(df_upload)
            
            # Abre o arquivo de log para adicionar os resultados
            with open(log_path, 'w', newline='', encoding='utf-8') as log_file:
                log_file.write("linha_original;query;codigo_encontrado;descricao_encontrada;status\n")

                # Itera sobre cada linha da planilha
                for index, row in df_upload.iterrows():
                    query = row['descricao']
                    status = "FALHA"
                    try:
                        payload = {"texto_busca": str(query), "top_k": 1}
                        response = requests.post(API_URL, json=payload, timeout=30)
                        
                        if response.status_code == 200:
                            results = response.json().get('results', [])
                            if results:
                                top_result = results[0]
                                # Preenche com os dados do primeiro resultado
                                df_upload.at[index, 'codigo_encontrado'] = top_result.get('codigo', 'N/A')
                                df_upload.at[index, 'fonte_encontrada'] = top_result.get('fonte', 'N/A')
                                df_upload.at[index, 'descricao_encontrada'] = top_result.get('descricao', 'N/A')
                                df_upload.at[index, 'unidade_encontrada'] = top_result.get('unidade', 'N/A')
                                df_upload.at[index, 'valor_unitario_encontrado'] = top_result.get('preco', 0.0)
                                status = "SUCESSO"
                            else:
                                status = "NENHUM_RESULTADO"
                        else:
                             status = f"ERRO_API_{response.status_code}"

                    except Exception as e:
                        status = f"ERRO_CONEXAO: {e}"

                    # Grava no arquivo de log
                    log_file.write(f"{index+1};{query};{df_upload.at[index, 'codigo_encontrado']};{df_upload.at[index, 'descricao_encontrada']};{status}\n")
                    
                    # Salva o arquivo Excel completo a cada 5 linhas (ou na última linha)
                    if (index + 1) % 5 == 0 or (index + 1) == total_rows:
                        df_upload.to_excel(temp_excel_path, index=False, engine='xlsxwriter')

                    # Atualiza a barra de progresso
                    progress_bar.progress((index + 1) / total_rows, text=f"Processando linha {index + 1}/{total_rows}... Progresso salvo.")

            st.success("Processamento concluído!")
            st.info(f"O resultado final foi salvo em '{temp_excel_path}'. Se o processo foi interrompido, você pode encontrar o progresso parcial neste mesmo arquivo.")
            
            # Oferece o arquivo final para download
            with open(temp_excel_path, "rb") as final_file:
                st.download_button(
                    label="📥 Baixar Planilha Processada Final",
                    data=final_file,
                    file_name="planilha_processada_final.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )