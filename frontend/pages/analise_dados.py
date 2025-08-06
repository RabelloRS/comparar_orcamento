import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import sys
from pathlib import Path

# Adiciona o diretório utils ao path
utils_dir = Path(__file__).parent.parent.parent / "utils"
sys.path.insert(0, str(utils_dir))

try:
    from logger import log_analysis, log_error, log_performance
except ImportError:
    # Fallback se o logger não estiver disponível
    def log_analysis(*args, **kwargs): pass
    def log_error(*args, **kwargs): pass
    def log_performance(*args, **kwargs): pass

def gerar_relatorio_precos(df_dados):
    """Gera relatório de análise de preços."""
    start_time = time.time()
    
    if df_dados is None or df_dados.empty:
        log_analysis("Geração de Relatório", records_count=0)
        return "Nenhum dado disponível para análise."
    
    try:
        log_analysis("Geração de Relatório", records_count=len(df_dados))
        
        # Análise básica
        total_itens = len(df_dados)
        preco_medio = df_dados['Preço'].mean() if 'Preço' in df_dados.columns else 0
        preco_min = df_dados['Preço'].min() if 'Preço' in df_dados.columns else 0
        preco_max = df_dados['Preço'].max() if 'Preço' in df_dados.columns else 0
        
        relatorio = f"""
        # 📊 Relatório de Análise de Preços
        
        **Data da Análise:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        ## Resumo Estatístico
        - **Total de Itens:** {total_itens}
        - **Preço Médio:** R$ {preco_medio:.2f}
        - **Preço Mínimo:** R$ {preco_min:.2f}
        - **Preço Máximo:** R$ {preco_max:.2f}
        - **Amplitude:** R$ {preco_max - preco_min:.2f}
        
        ## Observações
        - Dados analisados com base nos resultados da busca semântica
        - Valores podem variar conforme fonte e região
        """
        
        execution_time = time.time() - start_time
        log_performance("Geração de Relatório", execution_time)
        
        return relatorio
        
    except Exception as e:
        error_msg = f"Erro ao gerar relatório: {str(e)}"
        log_error("Análise de Dados", error_msg, e)
        return error_msg

def criar_grafico_precos(df_dados):
    """Cria gráfico de distribuição de preços."""
    start_time = time.time()
    
    if df_dados is None or df_dados.empty or 'Preço' not in df_dados.columns:
        log_analysis("Criação de Gráfico", records_count=0)
        # Retorna gráfico vazio
        fig = go.Figure()
        fig.add_annotation(
            text="Nenhum dado disponível para visualização",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title="Distribuição de Preços")
        return fig
    
    try:
        log_analysis("Criação de Gráfico", records_count=len(df_dados))
        
        # Cria histograma dos preços
        fig = px.histogram(
            df_dados, 
            x='Preço', 
            title='Distribuição de Preços dos Serviços',
            labels={'Preço': 'Preço (R$)', 'count': 'Frequência'},
            nbins=10
        )
        
        fig.update_layout(
            xaxis_title="Preço (R$)",
            yaxis_title="Frequência",
            showlegend=False
        )
        
        execution_time = time.time() - start_time
        log_performance("Criação de Gráfico", execution_time)
        
        return fig
        
    except Exception as e:
        error_msg = f"Erro ao criar gráfico: {str(e)}"
        log_error("Análise de Dados", error_msg, e)
        # Retorna gráfico de erro
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao criar gráfico: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=14, color="red")
        )
        fig.update_layout(title="Erro na Visualização")
        return fig

def exportar_dados(df_dados, formato):
    """Exporta dados em diferentes formatos."""
    start_time = time.time()
    
    if df_dados is None or df_dados.empty:
        log_analysis("Exportação de Dados", records_count=0)
        return None, "Nenhum dado disponível para exportação."
    
    try:
        log_analysis("Exportação de Dados", records_count=len(df_dados))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == "CSV":
            filename = f"analise_precos_{timestamp}.csv"
            df_dados.to_csv(filename, index=False, encoding='utf-8-sig')
            execution_time = time.time() - start_time
            log_performance("Exportação CSV", execution_time)
            return filename, f"Dados exportados para {filename}"
        
        elif formato == "Excel":
            filename = f"analise_precos_{timestamp}.xlsx"
            df_dados.to_excel(filename, index=False)
            execution_time = time.time() - start_time
            log_performance("Exportação Excel", execution_time)
            return filename, f"Dados exportados para {filename}"
        
        else:
            return None, "Formato não suportado."
            
    except Exception as e:
        error_msg = f"Erro ao exportar: {str(e)}"
        log_error("Análise de Dados", error_msg, e)
        return None, error_msg

# --- Interface da Página de Análise ---
with gr.Blocks() as analise_page:
    gr.Markdown("""
    ## 📈 Análise de Dados e Relatórios
    Analise os resultados das buscas e gere relatórios detalhados.
    """)
    
    # Estado compartilhado para dados
    dados_state = gr.State(value=pd.DataFrame())
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Dados para Análise")
            upload_dados = gr.File(
                label="Carregar arquivo CSV/Excel",
                file_types=[".csv", ".xlsx"],
                type="filepath"
            )
            
            carregar_btn = gr.Button("Carregar Dados", variant="secondary")
            
        with gr.Column(scale=2):
            gr.Markdown("### Visualização dos Dados")
            dados_preview = gr.DataFrame(
                label="Pré-visualização",
                interactive=False
            )
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Relatório de Análise")
            gerar_relatorio_btn = gr.Button("Gerar Relatório", variant="primary")
            relatorio_output = gr.Markdown("Carregue dados para gerar relatório.")
            
        with gr.Column():
            gr.Markdown("### Gráfico de Distribuição")
            grafico_output = gr.Plot(label="Distribuição de Preços")
    
    with gr.Row():
        gr.Markdown("### Exportação")
        formato_export = gr.Radio(
            choices=["CSV", "Excel"],
            value="CSV",
            label="Formato de Exportação"
        )
        exportar_btn = gr.Button("Exportar Dados", variant="secondary")
        export_status = gr.Markdown("")
        download_file = gr.File(label="Download", visible=False)
    
    # --- Funções de Callback ---
    def carregar_dados_callback(arquivo):
        if arquivo is None:
            return pd.DataFrame(), "Nenhum arquivo selecionado."
        
        try:
            if arquivo.endswith('.csv'):
                df = pd.read_csv(arquivo, encoding='utf-8-sig')
            elif arquivo.endswith('.xlsx'):
                df = pd.read_excel(arquivo)
            else:
                return pd.DataFrame(), "Formato de arquivo não suportado."
            
            return df, df
            
        except Exception as e:
            return pd.DataFrame(), f"Erro ao carregar arquivo: {str(e)}"
    
    # --- Eventos ---
    carregar_btn.click(
        fn=carregar_dados_callback,
        inputs=[upload_dados],
        outputs=[dados_state, dados_preview]
    )
    
    gerar_relatorio_btn.click(
        fn=gerar_relatorio_precos,
        inputs=[dados_state],
        outputs=[relatorio_output]
    )
    
    gerar_relatorio_btn.click(
        fn=criar_grafico_precos,
        inputs=[dados_state],
        outputs=[grafico_output]
    )
    
    exportar_btn.click(
        fn=exportar_dados,
        inputs=[dados_state, formato_export],
        outputs=[download_file, export_status]
    )

def create_interface():
    """Retorna a interface da página de análise de dados"""
    return analise_page

if __name__ == "__main__":
    # Para testar esta página individualmente
    analise_page.launch()