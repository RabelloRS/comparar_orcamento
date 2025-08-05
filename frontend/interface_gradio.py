import gradio as gr
import requests
import pandas as pd

# --- Constantes ---
API_URL = "http://localhost:8000/buscar"

def buscar_servico_handler(texto_busca, top_k):
    """Função para lidar com a chamada à API de busca."""
    if not texto_busca:
        return pd.DataFrame(), gr.Markdown("**Status:** Por favor, insira um texto para a busca.")

    try:
        payload = {"texto_busca": texto_busca, "top_k": int(top_k)}
        response = requests.post(API_URL, json=payload, timeout=60)

        if response.status_code == 200:
            results = response.json().get('results', [])
            if not results:
                return pd.DataFrame(), gr.Markdown("**Status:** Nenhum resultado encontrado.")
            
            # Converte os resultados para um DataFrame do Pandas
            df = pd.DataFrame(results)
            df_display = df[['codigo', 'descricao', 'preco', 'unidade', 'fonte', 'semantic_score']]
            df_display.rename(columns={
                'codigo': 'Código',
                'descricao': 'Descrição',
                'preco': 'Preço',
                'unidade': 'Unidade',
                'fonte': 'Fonte',
                'semantic_score': 'Score Semântico'
            }, inplace=True)
            
            status_md = f"**Status:** Encontrados {len(results)} resultados relevantes."
            return df_display, gr.Markdown(status_md)
        else:
            status_md = f"**Status:** Erro na API (Código: {response.status_code}). {response.text}"
            return pd.DataFrame(), gr.Markdown(status_md)

    except requests.exceptions.RequestException as e:
        status_md = f"**Status:** Erro de conexão com a API. Verifique se o backend está rodando. Detalhes: {e}"
        return pd.DataFrame(), gr.Markdown(status_md)

# --- Definição da Interface com Gradio ---
with gr.Blocks(theme=gr.themes.Soft(), title="Assistente de Orçamento de Obras") as demo:
    gr.Markdown("""
    # 🏗️ Assistente de Orçamento de Obras Públicas
    Sistema inteligente para busca e análise de serviços de construção civil.
    """)

    with gr.Tabs():
        with gr.TabItem("Busca Semântica Inteligente"):
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
            
            status_markdown = gr.Markdown("**Status:** Aguardando busca...")
            
            results_output = gr.DataFrame(
                headers=['Código', 'Descrição', 'Preço', 'Unidade', 'Fonte', 'Score Semântico'],
                datatype=['str', 'str', 'number', 'str', 'str', 'number'],
                label="Resultados da Busca"
            )

    # --- Lógica dos Componentes ---
    search_button.click(
        fn=buscar_servico_handler,
        inputs=[text_input, top_k_slider],
        outputs=[results_output, status_markdown]
    )

if __name__ == "__main__":
    # Para rodar esta interface: `python interface_gradio.py`
    # Certifique-se que o backend (main.py) está rodando em `localhost:8000`
    demo.launch()