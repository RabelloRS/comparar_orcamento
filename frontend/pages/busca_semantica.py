import gradio as gr
import requests
import pandas as pd
import time
import sys
from pathlib import Path

# Adiciona o diretório utils ao path
utils_dir = Path(__file__).parent.parent.parent / "utils"
sys.path.insert(0, str(utils_dir))

try:
    from logger import log_search, log_search_results, log_search_error, log_performance
except ImportError:
    # Fallback se o logger não estiver disponível
    def log_search(*args, **kwargs): pass
    def log_search_results(*args, **kwargs): pass
    def log_search_error(*args, **kwargs): pass
    def log_performance(*args, **kwargs): pass

# --- Constantes ---
API_URL = "http://127.0.0.1:8001/buscar"

def buscar_servico_handler(texto_busca, top_k):
    """Handler para realizar busca semântica."""
    if not texto_busca.strip():
        return pd.DataFrame(), gr.Markdown("**Status:** ❌ Por favor, insira um texto para busca."), ""
    
    start_time = time.time()
    processing_log_text = ""
    
    # Log da busca
    log_search(texto_busca, top_k)
    processing_log_text += f"🔍 Iniciando busca semântica para: '{texto_busca}'\n"
    processing_log_text += f"📊 Solicitando {top_k} resultados\n"
    
    try:
        payload = {
            "texto_busca": texto_busca,
            "top_k": top_k
        }
        
        processing_log_text += "🚀 Enviando requisição para a API...\n"
        
        request_start = time.time()
        response = requests.post(API_URL, json=payload, timeout=60)
        request_time = time.time() - request_start
        
        processing_log_text += f"⏱️ Tempo de requisição: {request_time:.2f}s\n"
        
        # Log da performance da requisição
        log_performance(f"API Request - {texto_busca[:50]}", request_time)

        if response.status_code == 200:
            processing_log_text += "✅ Resposta recebida com sucesso\n"
            processing_log_text += "🤖 Processando resultados da IA...\n"
            
            data = response.json()
            results = data.get('results', [])
            detailed_reasoning = data.get('detailed_reasoning', '')
            execution_time = time.time() - start_time
            
            if not results:
                log_search_results(texto_busca, 0, execution_time)
                processing_log_text += "❌ Nenhum resultado encontrado\n"
                return pd.DataFrame(), gr.Markdown("**Status:** Nenhum resultado encontrado."), processing_log_text
            
            # Log dos resultados
            log_search_results(texto_busca, len(results), execution_time)
            processing_log_text += f"📋 Encontrados {len(results)} resultados relevantes\n"
            processing_log_text += f"⚡ Tempo total de processamento: {execution_time:.2f}s\n"
            
            # Converte os resultados para um DataFrame do Pandas
            df = pd.DataFrame(results)
            df_display = df[['codigo', 'descricao', 'preco', 'unidade', 'fonte', 'score']].copy()
            df_display.rename(columns={
                'codigo': 'Código',
                'descricao': 'Descrição',
                'preco': 'Preço',
                'unidade': 'Unidade',
                'fonte': 'Fonte',
                'score': 'Score Semântico'
            }, inplace=True)
            
            processing_log_text += "🎯 Resultados formatados e prontos para exibição\n"
            
            # Adiciona o log detalhado de raciocínio da IA
            if detailed_reasoning:
                processing_log_text += "\n" + "="*50 + "\n"
                processing_log_text += "🧠 LOG DETALHADO DO RACIOCÍNIO DA IA:\n"
                processing_log_text += "="*50 + "\n"
                processing_log_text += detailed_reasoning + "\n"
                processing_log_text += "="*50 + "\n"
            
            status_md = f"**Status:** ✅ Busca realizada com sucesso! Encontrados {len(results)} resultados."
            return df_display, gr.Markdown(status_md), processing_log_text
        else:
            error_msg = f"Erro na API: {response.status_code} - {response.text}"
            processing_log_text += f"❌ {error_msg}\n"
            log_search_error(texto_busca, error_msg)
            return pd.DataFrame(), gr.Markdown(f"**Status:** ❌ {error_msg}"), processing_log_text
            
    except requests.exceptions.Timeout:
        error_msg = "Timeout: A busca demorou muito para responder"
        processing_log_text += f"⏰ {error_msg}\n"
        log_search_error(texto_busca, error_msg)
        return pd.DataFrame(), gr.Markdown(f"**Status:** ⏱️ {error_msg}"), processing_log_text
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Erro de conexão com a API. Verifique se o backend está rodando. Detalhes: {e}"
        processing_log_text += f"🔌 {error_msg}\n"
        log_search_error(texto_busca, error_msg)
        return pd.DataFrame(), gr.Markdown(f"**Status:** ❌ {error_msg}"), processing_log_text
        
    except Exception as e:
        error_msg = f"Erro inesperado: {str(e)}"
        processing_log_text += f"💥 {error_msg}\n"
        log_search_error(texto_busca, error_msg)
        return pd.DataFrame(), gr.Markdown(f"**Status:** ❌ {error_msg}"), processing_log_text

# --- Interface da Página de Busca Semântica ---
with gr.Blocks() as busca_page:
    gr.Markdown("""
    ## 🔍 Busca Semântica Inteligente
    Encontre serviços e insumos usando descrições em linguagem natural.
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(
                label="Descreva o serviço ou insumo desejado",
                placeholder="Ex: concreto usinado 30mpa para fundação",
                lines=2
            )
        with gr.Column(scale=1):
            top_k_slider = gr.Slider(
                minimum=1, 
                maximum=10, 
                value=3, 
                step=1, 
                label="Número de Resultados"
            )
    
    search_button = gr.Button("Buscar com IA", variant="primary")
    
    # Área de Status e Log de Processamento
    with gr.Row():
        with gr.Column(scale=1):
            status_markdown = gr.Markdown("**Status:** Aguardando busca...")
        with gr.Column(scale=2):
            processing_log = gr.Textbox(
                label="Log de Processamento e Raciocínio da IA",
                placeholder="Os detalhes do processamento e raciocínio da IA aparecerão aqui...",
                lines=8,
                max_lines=20,
                interactive=False
            )
    
    results_output = gr.DataFrame(
        headers=['Código', 'Descrição', 'Preço', 'Unidade', 'Fonte', 'Score Semântico'],
        datatype=['str', 'str', 'number', 'str', 'str', 'number'],
        label="Resultados da Busca"
    )
    
    # --- Lógica dos Componentes ---
    search_button.click(
        fn=buscar_servico_handler,
        inputs=[text_input, top_k_slider],
        outputs=[results_output, status_markdown, processing_log]
    )

def create_interface():
    """Retorna a interface da página de busca semântica"""
    return busca_page

if __name__ == "__main__":
    # Para testar esta página individualmente
    busca_page.launch()