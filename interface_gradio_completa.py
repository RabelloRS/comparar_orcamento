# interface_gradio_completa.py
import gradio as gr
import requests
import pandas as pd
import os
from datetime import datetime
import tempfile
import io

# --- Constantes ---
API_URL = "http://localhost:8000/buscar"
DATABASE_PATH = "dados/banco_dados_servicos.txt"
LOG_FILE = "processing_log.csv"
TEMP_DIR = "temp_files"

# Garante que o diretório de arquivos temporários exista
os.makedirs(TEMP_DIR, exist_ok=True)

def load_full_database():
    """Carrega o banco de dados completo de serviços em memória para a filtragem rápida."""
    try:
        df = pd.read_csv(DATABASE_PATH)
        df.rename(columns={'descricao_completa_do_servico_prestado': 'Descrição', 'codigo_da_composicao': 'Código'}, inplace=True)
        return df[['Código', 'Descrição']]
    except FileNotFoundError:
        return pd.DataFrame(columns=['Código', 'Descrição'])

# Carrega os dados uma vez
full_db = load_full_database()

def check_api_status():
    """Verifica o status da API"""
    try:
        api_status = requests.get("http://localhost:8000/", timeout=2)
        if api_status.status_code == 200:
            return "🟢 API conectada e funcionando"
        else:
            return "🟡 API respondendo com problemas"
    except requests.exceptions.RequestException:
        return "🔴 API desconectada\n\nPara iniciar o backend:\ncd app\npython -m uvicorn main:app --reload --port 8000"

def semantic_search(query, top_k):
    """Realiza busca semântica usando a API"""
    if not query.strip():
        return "Por favor, digite uma descrição para a busca.", None
    
    try:
        payload = {"texto_busca": query, "top_k": int(top_k)}
        response = requests.post(API_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            if not results:
                return "Nenhum resultado encontrado.", None
            else:
                # Formata os resultados para exibição
                formatted_results = []
                for item in results:
                    descricao_curta = item.get('descricao', 'N/A')
                    if '|' in descricao_curta:
                        descricao_curta = descricao_curta.split('|')[0].strip()
                    
                    result_dict = {
                        "Código": item.get('codigo', 'N/A'),
                        "Descrição": descricao_curta,
                        "Descrição Completa": item.get('descricao', 'N/A'),
                        "Preço Unitário": f"R$ {item.get('preco', 0.0):.2f}",
                        "Unidade": item.get('unidade', 'N/A'),
                        "Fonte": item.get('fonte', 'N/A'),
                        "Confiança": f"{item.get('score', 0.0):.4f}"
                    }
                    formatted_results.append(result_dict)
                
                status_msg = f"✅ Encontrados {len(results)} resultados relevantes"
                return status_msg, formatted_results
        
        elif response.status_code == 422:
            return "❌ Erro de validação: Verifique se os parâmetros estão corretos.", None
        elif response.status_code == 500:
            return "❌ Erro interno do servidor. Tente novamente em alguns instantes.", None
        else:
            return f"❌ Erro na API (Status: {response.status_code}): {response.text}", None
            
    except requests.exceptions.ConnectionError:
        return f"❌ Não foi possível conectar ao serviço de busca em {API_URL}.\n\n💡 Para usar a busca semântica:\n1. Abra um terminal\n2. Execute: cd app && python -m uvicorn main:app --reload --port 8000\n3. Aguarde a mensagem 'Aplicação pronta para receber requisições'", None
    except requests.exceptions.Timeout:
        return "⏱️ Timeout: A busca demorou mais que o esperado. Tente novamente.", None
    except requests.exceptions.RequestException as e:
        return f"❌ Erro de conexão: {str(e)}", None
    except Exception as e:
        return f"❌ Erro inesperado: {str(e)}", None

def filter_database(query):
    """Filtra o banco de dados em tempo real"""
    if not query.strip():
        return full_db.head(10)  # Mostra os 10 primeiros por padrão
    
    # Filtra o DataFrame em tempo real
    filtered_df = full_db[full_db['Descrição'].str.contains(query, case=False, na=False)]
    return filtered_df

def process_excel_file(file_path, progress=gr.Progress()):
    """Processa arquivo Excel em lote"""
    if file_path is None:
        return "Por favor, faça o upload de um arquivo Excel.", None, None
    
    try:
        # Lê o arquivo Excel
        df_upload = pd.read_excel(file_path)
        
        if 'descricao' not in df_upload.columns:
            return "❌ A planilha precisa ter uma coluna chamada 'descricao'. Por favor, ajuste e tente novamente.", None, None
        
        # Adiciona as novas colunas se não existirem
        for col in ['codigo_encontrado', 'fonte_encontrada', 'descricao_encontrada', 'unidade_encontrada', 'valor_unitario_encontrado']:
            if col not in df_upload.columns:
                df_upload[col] = ''
        
        # Gera nomes de arquivo únicos para esta sessão de processamento
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_excel_path = os.path.join(TEMP_DIR, f"processado_{timestamp}.xlsx")
        log_path = os.path.join(TEMP_DIR, f"log_{timestamp}.csv")
        
        total_rows = len(df_upload)
        processed_count = 0
        
        # Abre o arquivo de log para adicionar os resultados
        with open(log_path, 'w', newline='', encoding='utf-8') as log_file:
            log_file.write("linha_original;query;codigo_encontrado;descricao_encontrada;status\n")

            # Itera sobre cada linha da planilha
            for index, row in df_upload.iterrows():
                query = row['descricao']
                status = "FALHA"
                
                progress((index + 1) / total_rows, f"Processando linha {index + 1}/{total_rows}...")
                
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
                    df_upload.to_excel(temp_excel_path, index=False, engine='openpyxl')
                
                processed_count += 1

        success_msg = f"✅ Processamento concluído! {processed_count}/{total_rows} linhas processadas.\n\nO resultado foi salvo em '{temp_excel_path}'"
        
        return success_msg, df_upload, temp_excel_path
        
    except Exception as e:
        return f"❌ Erro no processamento: {str(e)}", None, None

def create_interface():
    """Cria a interface Gradio completa"""
    
    with gr.Blocks(
        title="Assistente de Orçamento de Obras",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 100% !important;
            width: 100% !important;
            padding: 15px !important;
        }
        .block {
            width: 100% !important;
        }
        """
    ) as demo:
        
        gr.Markdown(
            """
            # 🏗️ Assistente de Orçamento de Obras Públicas
            
            Sistema inteligente para busca e análise de serviços de construção civil
            """
        )
        
        # Status da API
        with gr.Row():
            api_status_display = gr.Textbox(
                label="Status da API",
                value=check_api_status(),
                interactive=False,
                lines=3
            )
            refresh_api_btn = gr.Button("🔄 Atualizar Status", variant="secondary")
        
        gr.Markdown("---")
        
        # Abas principais
        with gr.Tabs():
            # Aba 1: Busca Semântica
            with gr.TabItem("🔍 Busca Semântica (IA)"):
                gr.Markdown("### Use esta busca para encontrar serviços por contexto, sinônimos ou descrições incompletas.")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        semantic_query = gr.Textbox(
                            label="Descreva o serviço ou insumo desejado:",
                            placeholder="Ex: concreto para fundação",
                            lines=2
                        )
                        
                        top_k = gr.Slider(
                            label="Número de resultados a exibir:",
                            minimum=1,
                            maximum=10,
                            value=3,
                            step=1
                        )
                        
                        search_btn = gr.Button("🔍 Buscar com IA", variant="primary", size="lg")
                        
                        search_status = gr.Textbox(
                            label="Status da Busca",
                            interactive=False,
                            lines=3
                        )
                    
                    with gr.Column(scale=1):
                        search_results = gr.JSON(
                label="Resultados da Busca Semântica",
                visible=True
            )
            
            # Aba 2: Filtro Rápido
            with gr.TabItem("⚡ Filtro Rápido em Tempo Real"):
                gr.Markdown("### Digite qualquer parte do nome do serviço para filtrar a lista completa instantaneamente.")
                
                filter_query = gr.Textbox(
                    label="Digite para filtrar...",
                    placeholder="Ex: alvenaria bloco ceramico",
                    lines=1
                )
                
                filtered_results = gr.Dataframe(
                    label="Resultados Filtrados",
                    value=full_db.head(10),
                    interactive=False
                )
            
            # Aba 3: Processamento de Planilhas
            with gr.TabItem("📋 Processamento de Planilhas em Lote"):
                gr.Markdown(
                    """
                    ### Faça o upload de uma planilha Excel (.xlsx) com a coluna 'descricao'
                    
                    O sistema processará linha por linha, salvando o progresso continuamente.
                    """
                )
                
                with gr.Row():
                    with gr.Column(scale=1):
                        excel_file = gr.File(
                            label="Escolha uma planilha Excel",
                            file_types=[".xlsx"],
                            type="filepath"
                        )
                        
                        process_btn = gr.Button(
                            "📊 Iniciar Processamento Resiliente",
                            variant="primary",
                            size="lg"
                        )
                        
                        process_status = gr.Textbox(
                            label="Status do Processamento",
                            interactive=False,
                            lines=5
                        )
                    
                    with gr.Column(scale=1):
                        processed_preview = gr.Dataframe(
                            label="Pré-visualização dos Resultados",
                            interactive=False
                        )
                        
                        download_file = gr.File(
                            label="Arquivo Processado para Download",
                            visible=False
                        )
        
        # Eventos
        refresh_api_btn.click(
            fn=check_api_status,
            outputs=[api_status_display]
        )
        
        search_btn.click(
            fn=semantic_search,
            inputs=[semantic_query, top_k],
            outputs=[search_status, search_results]
        )
        
        semantic_query.submit(
            fn=semantic_search,
            inputs=[semantic_query, top_k],
            outputs=[search_status, search_results]
        )
        
        filter_query.change(
            fn=filter_database,
            inputs=[filter_query],
            outputs=[filtered_results]
        )
        
        def process_and_show_results(file_path, progress=gr.Progress()):
            status, df, file_path_result = process_excel_file(file_path, progress)
            
            if df is not None:
                # Mostra o arquivo para download
                return status, df, gr.update(value=file_path_result, visible=True)
            else:
                return status, None, gr.update(visible=False)
        
        process_btn.click(
            fn=process_and_show_results,
            inputs=[excel_file],
            outputs=[process_status, processed_preview, download_file]
        )
    
    return demo

def main():
    """Função principal"""
    print("============================================================")
    print("ASSISTENTE DE ORÇAMENTO DE OBRAS - INTERFACE GRADIO")
    print("============================================================")
    print()
    print("✅ Carregando interface...")
    
    demo = create_interface()
    
    print("🚀 Iniciando interface Gradio...")
    print()
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()