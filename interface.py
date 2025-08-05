# interface.py
import streamlit as st
import requests
import pandas as pd
import io
import os

# --- Configuração da Página ---
st.set_page_config(
    page_title="Assistente de Orçamento de Obras",
    page_icon="🏗️",
    layout="wide"
)

# --- Constantes e Cache ---
API_URL = "http://localhost:8000/buscar"
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "dados", "banco_dados_servicos.txt")  # Caminho absoluto para o banco de dados

@st.cache_data
def load_full_database():
    """
    Carrega o banco de dados completo de serviços em memória para a filtragem rápida.
    O decorador @st.cache_data garante que isso só será feito uma vez.
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(DATABASE_PATH):
            st.error(f"Arquivo do banco de dados não encontrado em '{DATABASE_PATH}'. A filtragem em tempo real está desativada.")
            return pd.DataFrame(columns=['Código', 'Descrição'])
        
        # Lê o arquivo CSV com o separador correto
        df = pd.read_csv(DATABASE_PATH, sep=',')
        
        # Verifica se as colunas necessárias existem
        required_columns = ['descricao_completa_do_servico_prestado', 'codigo_da_composicao']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Colunas necessárias não encontradas no banco de dados: {missing_columns}")
            return pd.DataFrame(columns=['Código', 'Descrição'])
        
        # Renomeia as colunas
        df.rename(columns={
            'descricao_completa_do_servico_prestado': 'Descrição', 
            'codigo_da_composicao': 'Código'
        }, inplace=True)
        
        return df[['Código', 'Descrição']]
        
    except Exception as e:
        st.error(f"Erro ao carregar o banco de dados: {str(e)}")
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

# Aguarde a mensagem: "Aplicação pronta para receber requisições"
        """, language="bash")

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
                                    c4.metric("Confiança", f"{item.get('semantic_score', 0.0):.4f}")
                    
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
            # Verifica se a API está disponível antes de processar
            try:
                test_response = requests.get("http://localhost:8000/", timeout=5)
                if test_response.status_code != 200:
                    st.error("❌ API não está respondendo. Inicie o backend antes de processar a planilha.")
                    st.stop()
            except requests.exceptions.RequestException:
                st.error("❌ Não foi possível conectar à API. Inicie o backend antes de processar a planilha.")
                st.info("💡 **Para iniciar o backend:**\n1. Abra um terminal\n2. Execute: `cd app && python -m uvicorn main:app --reload --port 8000`")
                st.stop()
            
            # Adiciona as novas colunas
            df_upload['codigo_encontrado'] = ''
            df_upload['fonte_encontrada'] = ''
            df_upload['descricao_encontrada'] = ''
            df_upload['unidade_encontrada'] = ''
            df_upload['valor_unitario_encontrado'] = ''
            df_upload['status_processamento'] = ''
            
            progress_bar = st.progress(0, text="Iniciando processamento...")
            total_rows = len(df_upload)
            errors_count = 0
            success_count = 0

            # Itera sobre cada linha da planilha
            for index, row in df_upload.iterrows():
                query = row['descricao']
                
                # Verifica se a descrição não está vazia
                if pd.isna(query) or str(query).strip() == '':
                    df_upload.at[index, 'codigo_encontrado'] = 'DESCRIÇÃO VAZIA'
                    df_upload.at[index, 'fonte_encontrada'] = 'ERRO'
                    df_upload.at[index, 'descricao_encontrada'] = 'ERRO'
                    df_upload.at[index, 'unidade_encontrada'] = 'ERRO'
                    df_upload.at[index, 'valor_unitario_encontrado'] = 'ERRO'
                    df_upload.at[index, 'status_processamento'] = 'ERRO: Descrição vazia'
                    errors_count += 1
                    continue
                
                try:
                    payload = {"texto_busca": str(query), "top_k": 1}
                    response = requests.post(API_URL, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        results = response.json().get('results', [])
                        if results:
                            # Preenche com os dados do primeiro resultado
                            result = results[0]
                            df_upload.at[index, 'codigo_encontrado'] = result.get('codigo', 'N/A')
                            df_upload.at[index, 'fonte_encontrada'] = result.get('fonte', 'N/A')
                            df_upload.at[index, 'descricao_encontrada'] = result.get('descricao', 'N/A')
                            df_upload.at[index, 'unidade_encontrada'] = result.get('unidade', 'N/A')
                            df_upload.at[index, 'valor_unitario_encontrado'] = result.get('preco', 0.0)
                            df_upload.at[index, 'status_processamento'] = 'SUCESSO'
                            success_count += 1
                        else:
                            df_upload.at[index, 'codigo_encontrado'] = 'SEM RESULTADO'
                            df_upload.at[index, 'fonte_encontrada'] = 'N/A'
                            df_upload.at[index, 'descricao_encontrada'] = 'N/A'
                            df_upload.at[index, 'unidade_encontrada'] = 'N/A'
                            df_upload.at[index, 'valor_unitario_encontrado'] = 0.0
                            df_upload.at[index, 'status_processamento'] = 'SEM RESULTADO'
                            errors_count += 1
                    else:
                        df_upload.at[index, 'codigo_encontrado'] = f'ERRO API {response.status_code}'
                        df_upload.at[index, 'fonte_encontrada'] = 'ERRO'
                        df_upload.at[index, 'descricao_encontrada'] = 'ERRO'
                        df_upload.at[index, 'unidade_encontrada'] = 'ERRO'
                        df_upload.at[index, 'valor_unitario_encontrado'] = 'ERRO'
                        df_upload.at[index, 'status_processamento'] = f'ERRO: API retornou {response.status_code}'
                        errors_count += 1
                        
                except Exception as e:
                    # Se houver erro, preenche com informações do erro
                    df_upload.at[index, 'codigo_encontrado'] = 'ERRO CONEXÃO'
                    df_upload.at[index, 'fonte_encontrada'] = 'ERRO'
                    df_upload.at[index, 'descricao_encontrada'] = 'ERRO'
                    df_upload.at[index, 'unidade_encontrada'] = 'ERRO'
                    df_upload.at[index, 'valor_unitario_encontrado'] = 'ERRO'
                    df_upload.at[index, 'status_processamento'] = f'ERRO: {str(e)[:50]}...'
                    errors_count += 1

                # Atualiza a barra de progresso
                progress_bar.progress((index + 1) / total_rows, text=f"Processando linha {index + 1}/{total_rows}...")

            # Mostra estatísticas do processamento
            if success_count > 0:
                st.success(f"✅ Planilha processada! {success_count} sucessos, {errors_count} erros.")
            else:
                st.warning(f"⚠️ Processamento concluído com problemas: {success_count} sucessos, {errors_count} erros.")
            
            st.write("Resultado final:")
            st.dataframe(df_upload)

            # Cria um botão para download do arquivo processado
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_upload.to_excel(writer, index=False, sheet_name='Resultados')
                
                st.download_button(
                    label="📥 Baixar Planilha Processada",
                    data=output.getvalue(),
                    file_name="planilha_processada.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Erro ao gerar arquivo para download: {str(e)}")