import gradio as gr
import requests
import json
from datetime import datetime
import time
import sys
from pathlib import Path

# Adiciona o diretório utils ao path
utils_dir = Path(__file__).parent.parent.parent / "utils"
sys.path.insert(0, str(utils_dir))

try:
    from logger import log_config, log_error, log_performance, log_api
except ImportError:
    # Fallback se o logger não estiver disponível
    def log_config(*args, **kwargs): pass
    def log_error(*args, **kwargs): pass
    def log_performance(*args, **kwargs): pass
    def log_api(*args, **kwargs): pass

# --- Constantes ---
API_BASE_URL = "http://localhost:8000"
CONFIG_FILE = "config.json"

def verificar_status_api():
    """Verifica o status da API backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return "🟢 **API Online** - Conectado com sucesso", "success"
        else:
            return f"🟡 **API com Problemas** - Código: {response.status_code}", "warning"
    except requests.exceptions.RequestException:
        return "🔴 **API Offline** - Não foi possível conectar", "error"

def carregar_configuracoes():
    """Carrega configurações do arquivo JSON."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return (
            config.get('api_url', API_BASE_URL),
            config.get('timeout', 60),
            config.get('max_results', 10),
            config.get('theme', 'soft'),
            config.get('auto_save', True)
        )
    except FileNotFoundError:
        # Configurações padrão
        return API_BASE_URL, 60, 10, 'soft', True
    except Exception as e:
        return f"Erro ao carregar: {e}", 60, 10, 'soft', True

def salvar_configuracoes(api_url, timeout, max_results, theme, auto_save):
    """Salva configurações no arquivo JSON."""
    try:
        # Carrega configurações antigas para comparação
        old_config = carregar_configuracoes()
        
        config = {
            'api_url': api_url,
            'timeout': int(timeout),
            'max_results': int(max_results),
            'theme': theme,
            'auto_save': auto_save,
            'last_updated': datetime.now().isoformat()
        }
        
        # Log das mudanças
        if isinstance(old_config, tuple):
            old_config_dict = {
                'api_url': old_config[0],
                'timeout': old_config[1],
                'max_results': old_config[2],
                'theme': old_config[3],
                'auto_save': old_config[4]
            }
            
            for key, new_value in config.items():
                if key != "last_updated" and key in old_config_dict:
                    old_value = old_config_dict[key]
                    if old_value != new_value:
                        log_config(key, old_value, new_value)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return "✅ Configurações salvas com sucesso!"
    except Exception as e:
        error_msg = f"Erro ao salvar configurações: {e}"
        log_error("Configurações", error_msg, e)
        return f"❌ {error_msg}"

def resetar_configuracoes():
    """Reseta configurações para os valores padrão."""
    try:
        config_padrao = {
            'api_url': API_BASE_URL,
            'timeout': 60,
            'max_results': 10,
            'theme': 'soft',
            'auto_save': True,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_padrao, f, indent=2, ensure_ascii=False)
        
        return (
            config_padrao['api_url'],
            config_padrao['timeout'],
            config_padrao['max_results'],
            config_padrao['theme'],
            config_padrao['auto_save'],
            "🔄 Configurações resetadas para os valores padrão!"
        )
    except Exception as e:
        return API_BASE_URL, 60, 10, 'soft', True, f"❌ Erro ao resetar: {e}"

def testar_conexao_api(api_url, timeout):
    """Testa a conexão com a API usando as configurações fornecidas."""
    try:
        start_time = time.time()
        response = requests.get(f"{api_url}/health", timeout=int(timeout))
        response_time = time.time() - start_time
        
        # Log da requisição
        log_api("/health", "GET", response.status_code, response_time)
        
        if response.status_code == 200:
            return f"✅ Conexão bem-sucedida!\n⏱️ Tempo de resposta: {response_time:.3f}s\n📡 Status: {response.status_code}"
        else:
            return f"⚠️ API respondeu com status {response.status_code}\n⏱️ Tempo: {response_time:.3f}s"
            
    except requests.exceptions.Timeout:
        log_error("Configurações", "Timeout na conexão com API")
        return "⏱️ Timeout: A API não respondeu no tempo esperado"
    except requests.exceptions.ConnectionError:
        log_error("Configurações", "Erro de conexão com API")
        return "❌ Erro de conexão: Não foi possível conectar à API"
    except Exception as e:
        error_msg = f"Erro inesperado ao testar API: {str(e)}"
        log_error("Configurações", error_msg, e)
        return f"❌ Erro inesperado: {str(e)}"

def obter_info_sistema():
    """Obtém informações do sistema."""
    try:
        response = requests.get(f"{API_BASE_URL}/info", timeout=10)
        if response.status_code == 200:
            info = response.json()
            return f"""
            ### 📋 Informações do Sistema
            
            **Versão da API:** {info.get('version', 'N/A')}
            **Status:** {info.get('status', 'N/A')}
            **Uptime:** {info.get('uptime', 'N/A')}
            **Banco de Dados:** {info.get('database_status', 'N/A')}
            **Última Atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
        else:
            return "❌ Não foi possível obter informações do sistema"
    except Exception as e:
        return f"❌ Erro ao obter informações: {e}"

# --- Interface da Página de Configurações ---
with gr.Blocks() as config_page:
    gr.Markdown("""
    ## ⚙️ Configurações do Sistema
    Configure parâmetros da aplicação e monitore o status da API.
    """)
    
    with gr.Tabs():
        with gr.TabItem("🔧 Configurações Gerais"):
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("### Configurações da API")
                    
                    api_url_input = gr.Textbox(
                        label="URL da API",
                        value=API_BASE_URL,
                        placeholder="http://localhost:8000"
                    )
                    
                    timeout_input = gr.Number(
                        label="Timeout (segundos)",
                        value=60,
                        minimum=5,
                        maximum=300
                    )
                    
                    max_results_input = gr.Number(
                        label="Máximo de Resultados",
                        value=10,
                        minimum=1,
                        maximum=50
                    )
                    
                with gr.Column(scale=1):
                    gr.Markdown("### Preferências")
                    
                    theme_input = gr.Radio(
                        choices=["soft", "default", "monochrome"],
                        value="soft",
                        label="Tema da Interface"
                    )
                    
                    auto_save_input = gr.Checkbox(
                        label="Salvamento Automático",
                        value=True
                    )
            
            with gr.Row():
                carregar_config_btn = gr.Button("Carregar Configurações", variant="secondary")
                salvar_config_btn = gr.Button("Salvar Configurações", variant="primary")
                resetar_config_btn = gr.Button("Resetar Padrões", variant="stop")
            
            config_status = gr.Markdown("")
        
        with gr.TabItem("🔍 Status e Testes"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Status da API")
                    verificar_status_btn = gr.Button("Verificar Status", variant="primary")
                    status_output = gr.Markdown("Clique para verificar o status da API")
                    
                    gr.Markdown("### Teste de Conexão")
                    testar_conexao_btn = gr.Button("Testar Conexão", variant="secondary")
                    teste_output = gr.Markdown("")
                
                with gr.Column():
                    gr.Markdown("### Informações do Sistema")
                    obter_info_btn = gr.Button("Obter Informações", variant="secondary")
                    info_output = gr.Markdown("Clique para obter informações do sistema")
        
        with gr.TabItem("📚 Ajuda"):
            gr.Markdown("""
            ### 🆘 Guia de Configuração
            
            #### Configurações da API
            - **URL da API:** Endereço onde o backend está rodando (padrão: http://localhost:8000)
            - **Timeout:** Tempo limite para requisições em segundos
            - **Máximo de Resultados:** Número máximo de resultados retornados nas buscas
            
            #### Temas Disponíveis
            - **Soft:** Interface suave e moderna (recomendado)
            - **Default:** Tema padrão do Gradio
            - **Monochrome:** Interface em tons de cinza
            
            #### Solução de Problemas
            
            **🔴 API Offline:**
            1. Verifique se o backend está rodando
            2. Confirme a URL da API
            3. Verifique a conectividade de rede
            
            **⏱️ Timeout:**
            1. Aumente o valor do timeout
            2. Verifique a performance do servidor
            3. Teste a conexão de rede
            
            **❌ Erro de Configuração:**
            1. Use o botão "Resetar Padrões"
            2. Verifique as permissões de arquivo
            3. Reinicie a aplicação
            """)
    
    # --- Eventos ---
    carregar_config_btn.click(
        fn=carregar_configuracoes,
        outputs=[api_url_input, timeout_input, max_results_input, theme_input, auto_save_input]
    )
    
    salvar_config_btn.click(
        fn=salvar_configuracoes,
        inputs=[api_url_input, timeout_input, max_results_input, theme_input, auto_save_input],
        outputs=[config_status]
    )
    
    resetar_config_btn.click(
        fn=resetar_configuracoes,
        outputs=[api_url_input, timeout_input, max_results_input, theme_input, auto_save_input, config_status]
    )
    
    verificar_status_btn.click(
        fn=lambda: verificar_status_api()[0],
        outputs=[status_output]
    )
    
    testar_conexao_btn.click(
        fn=testar_conexao_api,
        inputs=[api_url_input, timeout_input],
        outputs=[teste_output]
    )
    
    obter_info_btn.click(
        fn=obter_info_sistema,
        outputs=[info_output]
    )

def create_interface():
    """Retorna a interface da página de configurações"""
    return config_page

if __name__ == "__main__":
    # Para testar esta página individualmente
    config_page.launch()