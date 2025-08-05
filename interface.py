# interface.py
import streamlit as st
import requests
import pandas as pd
import io

# --- Configuração da Página ---
st.set_page_config(
    page_title="Assistente de Orçamento de Obras",
    page_icon="🏗️",
    layout="wide"
)

# --- Constantes e Cache ---
API_URL = "http://localhost:8000/buscar"
DATABASE_PATH = "dados/banco_dados_servicos.txt" # Caminho para o banco de dados completo

@st.cache_data
def load_full_database():
    """
    Carrega o banco de dados completo de serviços em memória para a filtragem rápida.
    O decorador @st.cache_data garante que isso só será feito uma vez.
    """
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
                                with st.expander(f"**{item['codigo']}** - {item['descricao'].split('|')[0].strip()}"):
                                    st.markdown(f"**Descrição Completa:** {item['descricao']}")
                                    st.markdown("---")
                                    c1, c2, c3, c4 = st.columns(4)
                                    c1.metric("Preço Unitário", f"R$ {item.get('preco', 0.0):.2f}")
                                    c2.metric("Unidade", item.get('unidade', 'N/A'))
                                    c3.metric("Fonte", item.get('fonte', 'N/A'))
                                    c4.metric("Confiança", f"{item.get('semantic_score', 0.0):.4f}")
                    else:
                        st.error(f"Erro na API (Status: {response.status_code}).")
                except requests.RequestException:
                    st.error(f"Não foi possível conectar ao serviço de busca em {API_URL}. O backend está rodando?")


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


# --- SEÇÃO 3: PROCESSAMENTO DE PLANILHAS EM LOTE ---
st.markdown("\n---\n")
st.header("📋 Processamento de Planilhas em Lote")
st.info("Faça o upload de uma planilha Excel (.xlsx) com a coluna 'descricao' e o sistema irá preencher o 'codigo' e a 'fonte' automaticamente.")

uploaded_file = st.file_uploader("Escolha uma planilha Excel", type=["xlsx"])

if uploaded_file is not None:
    df_upload = pd.read_excel(uploaded_file)
    st.write("Pré-visualização da sua planilha:")
    st.dataframe(df_upload.head())

    # Verifica se a coluna 'descricao' existe
    if 'descricao' not in df_upload.columns:
        st.error("A planilha precisa ter uma coluna chamada 'descricao'. Por favor, ajuste e tente novamente.")
    else:
        if st.button("Processar Planilha Completa", type="primary"):
            # Adiciona as novas colunas
            df_upload['codigo_encontrado'] = ''
            df_upload['fonte_encontrada'] = ''
            df_upload['descricao_encontrada'] = ''
            df_upload['unidade_encontrada'] = ''
            df_upload['valor_unitario_encontrado'] = ''
            
            progress_bar = st.progress(0, text="Iniciando processamento...")
            total_rows = len(df_upload)

            # Itera sobre cada linha da planilha
            for index, row in df_upload.iterrows():
                query = row['descricao']
                try:
                    payload = {"texto_busca": str(query), "top_k": 1}
                    response = requests.post(API_URL, json=payload, timeout=30)
                    if response.status_code == 200:
                        results = response.json().get('results', [])
                        if results:
                            # Preenche com os dados do primeiro resultado
                            result = results[0]
                            df_upload.at[index, 'codigo_encontrado'] = result['codigo']
                            df_upload.at[index, 'fonte_encontrada'] = result['fonte']
                            df_upload.at[index, 'descricao_encontrada'] = result.get('descricao', 'N/A')
                            df_upload.at[index, 'unidade_encontrada'] = result.get('unidade', 'N/A')
                            df_upload.at[index, 'valor_unitario_encontrado'] = result.get('preco', 0.0)
                except Exception:
                    # Se houver erro, preenche com um aviso
                    df_upload.at[index, 'codigo_encontrado'] = 'ERRO'
                    df_upload.at[index, 'fonte_encontrada'] = 'ERRO'
                    df_upload.at[index, 'descricao_encontrada'] = 'ERRO'
                    df_upload.at[index, 'unidade_encontrada'] = 'ERRO'
                    df_upload.at[index, 'valor_unitario_encontrado'] = 'ERRO'

                # Atualiza a barra de progresso
                progress_bar.progress((index + 1) / total_rows, text=f"Processando linha {index + 1}/{total_rows}...")

            st.success("Planilha processada com sucesso!")
            st.write("Resultado final:")
            st.dataframe(df_upload)

            # Cria um botão para download do arquivo processado
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_upload.to_excel(writer, index=False, sheet_name='Resultados')
            
            st.download_button(
                label="📥 Baixar Planilha Processada",
                data=output.getvalue(),
                file_name="planilha_processada.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )