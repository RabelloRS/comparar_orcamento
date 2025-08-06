#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import time
import requests
import psutil
import gradio as gr
import json
from pathlib import Path

# Adiciona o diretório do projeto ao path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(app_dir / "backend"))
sys.path.insert(0, str(app_dir / "frontend"))
sys.path.insert(0, str(app_dir / "utils"))

# Importa o sistema de logs
try:
    from logger import log_backend, log_system, log_error, log_api, log_performance
except ImportError:
    # Fallback se o logger não estiver disponível
    def log_backend(*args, **kwargs): pass
    def log_system(*args, **kwargs): pass
    def log_error(*args, **kwargs): pass
    def log_api(*args, **kwargs): pass
    def log_performance(*args, **kwargs): pass

# Importa as páginas modulares
try:
    from pages.busca_semantica import create_interface as create_busca_semantica_interface
    from pages.analise_dados import create_interface as create_analise_dados_interface
    from pages.configuracoes import create_interface as create_configuracoes_interface
    MODULAR_PAGES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Páginas modulares não disponíveis: {e}")
    MODULAR_PAGES_AVAILABLE = False

class BackendController:
    def __init__(self):
        self.backend_process = None
        self.backend_url = "http://127.0.0.1:8001"
        
    def check_backend_status(self):
        """Verifica se o backend está rodando"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.backend_url}/health", timeout=3)
            response_time = time.time() - start_time
            
            # Log da verificação
            log_api("/health", "GET", response.status_code, response_time)
            
            if response.status_code == 200:
                # Verifica se é o processo que este painel está gerenciando
                if self.backend_process and self.backend_process.poll() is None:
                    log_backend("Status Check", "Online (Gerenciado)")
                    return "🟢 Backend Online (Gerenciado)", "success"
                else:
                    log_backend("Status Check", "Online (Externo)")
                    return "🟡 Backend Online (Externo)", "warning"
            else:
                log_backend("Status Check", f"Com problemas - Status {response.status_code}")
                return "🔴 Backend com Problemas", "warning"
        except requests.exceptions.RequestException as e:
            # Verifica se ainda há processo rodando
            if self.backend_process and self.backend_process.poll() is None:
                log_backend("Status Check", "Iniciando...")
                return "🔴 Backend Iniciando...", "warning"
            log_backend("Status Check", "Offline")
            log_error("Backend Controller", f"Erro de conexão: {str(e)}", e)
            return "🔴 Backend Offline", "error"
    
    def start_backend(self):
        """Inicia o backend"""
        if self.backend_process and self.backend_process.poll() is None:
            log_backend("Start", "Tentativa de iniciar backend já rodando")
            return "⚠️ Backend já está rodando!"
        
        try:
            start_time = time.time()
            log_backend("Start", "Iniciando processo do backend")
            
            cmd = [sys.executable, "-m", "uvicorn", "backend.app.main:app", 
                   "--host", "127.0.0.1", "--port", "8000", "--reload"]
            
            self.backend_process = subprocess.Popen(
                cmd, 
                cwd=app_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Aguarda um pouco para o backend inicializar
            time.sleep(3)
            
            status, _ = self.check_backend_status()
            if "Online" in status:
                startup_time = time.time() - start_time
                log_backend("Start", "Backend iniciado com sucesso")
                log_performance("Backend Startup", startup_time)
                return "✅ Backend iniciado com sucesso!"
            else:
                log_error("Backend Controller", "Erro ao iniciar backend")
                return "❌ Erro ao iniciar backend"
                
        except Exception as e:
            error_msg = f"Erro ao iniciar backend: {str(e)}"
            log_error("Backend Controller", error_msg, e)
            return f"❌ {error_msg}"
    
    def find_external_backend_processes(self):
        """Encontra processos backend externos rodando na porta 8000"""
        external_processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('uvicorn' in str(cmd) and '8000' in str(cmd) for cmd in cmdline):
                        if not self.backend_process or proc.info['pid'] != self.backend_process.pid:
                            external_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return external_processes
    
    def stop_backend(self):
        """Para o backend"""
        messages = []
        log_backend("Stop", "Iniciando parada do backend")
        
        # Para o processo gerenciado por este painel
        if self.backend_process and self.backend_process.poll() is None:
            try:
                log_backend("Stop", "Parando processo gerenciado")
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                log_backend("Stop", "Backend gerenciado parado com sucesso")
                messages.append("🛑 Backend gerenciado parado com sucesso!")
            except subprocess.TimeoutExpired:
                log_backend("Stop", "Forçando parada do processo gerenciado")
                self.backend_process.kill()
                messages.append("🛑 Backend gerenciado forçadamente parado!")
            except Exception as e:
                log_error("Backend Controller", f"Erro ao parar backend gerenciado: {str(e)}", e)
                messages.append(f"❌ Erro ao parar backend gerenciado: {str(e)}")
        
        # Verifica e para processos externos
        external_processes = self.find_external_backend_processes()
        for proc in external_processes:
            try:
                log_backend("Stop", f"Parando processo externo PID: {proc.pid}")
                proc.terminate()
                proc.wait(timeout=3)
                messages.append(f"🛑 Processo externo (PID: {proc.pid}) parado!")
            except (psutil.TimeoutExpired, psutil.NoSuchProcess):
                try:
                    log_backend("Stop", f"Forçando parada do processo externo PID: {proc.pid}")
                    proc.kill()
                    messages.append(f"🛑 Processo externo (PID: {proc.pid}) forçadamente parado!")
                except:
                    log_error("Backend Controller", f"Não foi possível parar processo PID: {proc.pid}")
                    messages.append(f"❌ Não foi possível parar processo PID: {proc.pid}")
            except Exception as e:
                log_error("Backend Controller", f"Erro ao parar processo externo: {str(e)}", e)
                messages.append(f"❌ Erro ao parar processo externo: {str(e)}")
        
        if not messages:
            log_backend("Stop", "Nenhum backend encontrado rodando")
            return "⚠️ Nenhum backend encontrado rodando!"
        
        log_backend("Stop", "Parada do backend concluída")
        return "\n".join(messages)
    
    def restart_backend(self):
        """Reinicia o backend"""
        stop_msg = self.stop_backend()
        time.sleep(2)
        start_msg = self.start_backend()
        return f"{stop_msg}\n{start_msg}"

# Instância global do controlador
controller = BackendController()

def get_system_info():
    """Obtém informações do sistema"""
    try:
        start_time = time.time()
        
        # Informações de CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Informações de memória
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used / (1024**3)  # GB
        memory_total = memory.total / (1024**3)  # GB
        
        # Informações de disco
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used = disk.used / (1024**3)  # GB
        disk_total = disk.total / (1024**3)  # GB
        
        # Log das informações do sistema
        system_data = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent
        }
        log_system("System Info", str(system_data))
        
        collection_time = time.time() - start_time
        log_performance("System Info Collection", collection_time)
        
        return f"""📊 **Informações do Sistema**
        
🖥️ **CPU**: {cpu_percent}% ({cpu_count} cores)
💾 **Memória**: {memory_percent}% ({memory_used:.1f}GB / {memory_total:.1f}GB)
💿 **Disco**: {disk_percent}% ({disk_used:.1f}GB / {disk_total:.1f}GB)
        """
        
    except Exception as e:
        error_msg = f"Erro ao obter informações do sistema: {str(e)}"
        log_error("System Monitor", error_msg, e)
        return f"❌ {error_msg}"

def create_dashboard():
    """Cria o painel de controle do projeto"""
    
    with gr.Blocks(
        title="Painel de Controle - Sistema de Orçamento", 
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 100% !important;
            width: 100% !important;
            padding: 10px !important;
        }
        .block {
            width: 100% !important;
        }
        .gr-row {
            width: 100% !important;
            gap: 15px !important;
        }
        .gr-column {
            min-width: 0 !important;
            flex: 1 !important;
        }
        .gr-form {
            width: 100% !important;
        }
        .gr-box {
            width: 100% !important;
        }
        """
    ) as demo:
        gr.Markdown(
            """
            #  Orçamento - Construção Civil
            ## Painel de Controle do Projeto
            """
        )
        
        # Abas principais no topo
        with gr.Tabs():
            # Aba 1: Controle do Sistema
            with gr.TabItem("Controle do Sistema"):
                # Layout em 2 colunas para controle do sistema
                with gr.Row(equal_height=True):
                    # Coluna 1: Controle do Backend
                    with gr.Column(scale=1, min_width=400):
                        gr.Markdown("### 🎛️ Controle do Backend")
                        
                        # Status do Backend
                        with gr.Row():
                            status_display = gr.Textbox(
                                label="Status do Backend",
                                value="Verificando...",
                                interactive=False,
                                elem_classes=["status-display"],
                                scale=3
                            )
                            restart_interface_btn = gr.Button("🔄 Reiniciar Interface", variant="secondary", size="sm", scale=1)
                        
                        # Botões de controle
                        with gr.Row():
                            start_btn = gr.Button("🚀 Iniciar", variant="primary", size="sm")
                            restart_btn = gr.Button("🔄 Reiniciar", variant="secondary", size="sm")
                            stop_btn = gr.Button("🛑 Parar", variant="stop", size="sm")
                        
                        # Botão para atualizar status
                        refresh_btn = gr.Button("🔄 Atualizar Status", size="sm")
                        
                        # Log de ações
                        action_log = gr.Textbox(
                            label="Log de Ações",
                            lines=8,
                            interactive=False,
                            placeholder="As ações aparecerão aqui..."
                        )
                        
            
                    
            
            # Aba 2: Teste de Pesquisa
            with gr.TabItem("🔍 Teste de Pesquisa"):
                gr.Markdown("### 🔍 Teste de Pesquisa do Sistema")
                
                # Layout em 2 colunas para teste de pesquisa
                with gr.Row(equal_height=True):
                    # Coluna 1: Entrada de pesquisa
                    with gr.Column(scale=1, min_width=400):
                        gr.Markdown("#### Configuração da Pesquisa")
                        
                        # Campo de pesquisa
                        search_input = gr.Textbox(
                            label="Texto para Busca",
                            placeholder="Digite aqui o que deseja pesquisar...",
                            lines=3
                        )
                        
                        # Configurações da busca
                        with gr.Row():
                            top_k = gr.Number(
                                label="Número de Resultados",
                                value=3,
                                minimum=1,
                                maximum=10,
                                step=1
                            )
                        
                        # Botão de pesquisa
                        search_btn = gr.Button("🔍 Pesquisar", variant="primary", size="lg")
                        
                        # Status da pesquisa
                        search_status = gr.Textbox(
                            label="Status da Pesquisa",
                            interactive=False,
                            lines=3
                        )
                        
                    # Coluna 2: Resultados da pesquisa
                    with gr.Column(scale=1, min_width=400):
                        gr.Markdown("#### Resultados da Pesquisa")
                        
                        # Resultados da pesquisa
                        search_results = gr.JSON(
                            label="Resultados da Pesquisa",
                            visible=True
                        )
            
            # Aba 3: Controle Avançado dos Agentes
            with gr.TabItem("🤖 Controle dos Agentes"):
                gr.Markdown("### 🤖 Painel de Controle e Orientação dos Agentes de IA")
                
                # Layout em 2 colunas
                with gr.Row(equal_height=True):
                    # Coluna 1: Configuração dos Agentes
                    with gr.Column(scale=1, min_width=400):
                        gr.Markdown("#### ⚙️ Configuração dos Agentes")
                        
                        # Seletor de agente
                        agent_selector = gr.Dropdown(
                            choices=["classifier", "reasoner", "finder"],
                            value="reasoner",
                            label="Agente para Configurar",
                            info="Selecione o agente que deseja configurar"
                        )
                        
                        # Editor de prompt base
                        base_prompt_editor = gr.Textbox(
                            label="Prompt Base do Agente",
                            lines=8,
                            placeholder="O prompt base será carregado aqui...",
                            info="Edite o prompt base que define o comportamento do agente"
                        )
                        
                        # Editor de orientação do usuário
                        user_guidance_editor = gr.Textbox(
                            label="Orientação Manual (Opcional)",
                            lines=4,
                            placeholder="Digite orientações específicas para refinar o comportamento...",
                            info="Orientações adicionais que serão aplicadas durante a execução"
                        )
                        
                        # Configuração de prioridades do projeto
                        project_profile_editor = gr.Textbox(
                            label="Perfil do Projeto",
                            lines=3,
                            placeholder="Ex: residencial, comercial, industrial...",
                            info="Define o tipo de projeto para ajustar prioridades"
                        )
                        
                        # Botões de controle
                        with gr.Row():
                            load_config_btn = gr.Button("📥 Carregar Config", variant="secondary", size="sm")
                            save_config_btn = gr.Button("💾 Salvar Config", variant="primary", size="sm")
                            reset_config_btn = gr.Button("🔄 Resetar", variant="stop", size="sm")
                        
                        # Status da configuração
                        config_status = gr.Textbox(
                            label="Status da Configuração",
                            interactive=False,
                            lines=2
                        )
                    
                    # Coluna 2: Teste e Análise
                    with gr.Column(scale=1, min_width=400):
                        gr.Markdown("#### 🧪 Teste e Análise em Tempo Real")
                        
                        # Campo de teste
                        test_query = gr.Textbox(
                            label="Query de Teste",
                            placeholder="Digite uma consulta para testar o agente...",
                            lines=3
                        )
                        
                        # Botão de teste
                        test_agent_btn = gr.Button("🧪 Testar Agente", variant="primary", size="lg")
                        
                        # Resultados do teste
                        test_results = gr.JSON(
                            label="Resultados do Teste",
                            visible=True
                        )
                        
                        # Trace detalhado
                        trace_display = gr.JSON(
                            label="Trace Detalhado da Execução",
                            visible=True
                        )
                        
                        # Log de auditoria
                        audit_log = gr.Textbox(
                            label="Log de Auditoria",
                            lines=6,
                            interactive=False,
                            placeholder="Logs de auditoria aparecerão aqui..."
                        )
            
            # Abas modulares (se disponíveis)
            if MODULAR_PAGES_AVAILABLE:
                # Aba 3: Busca Semântica Avançada
                with gr.TabItem("🔍 Busca Semântica"):
                    busca_interface = create_busca_semantica_interface()
                    busca_interface.render()
                
                # Aba 4: Análise de Dados
                with gr.TabItem("📊 Análise de Dados"):
                    analise_interface = create_analise_dados_interface()
                    analise_interface.render()
                
                # Aba 5: Configurações
                with gr.TabItem("⚙️ Configurações"):
                    config_interface = create_configuracoes_interface()
                    config_interface.render()
            
            # Aba: Sobre o Sistema
            with gr.TabItem("ℹ️ Sobre"):
                gr.Markdown(
                    """
                    # 📋 Sistema de Orçamento - Construção Civil
                    
                    ## 🎯 Funcionalidades Principais
                    
                    ### 🎛️ Controle do Sistema
                    - **Gerenciamento do Backend**: Iniciar, parar e reiniciar o servidor backend
                    - **Monitoramento**: Status em tempo real do sistema
                    - **Logs**: Acompanhamento das ações realizadas
                    
                    ### 🔍 Pesquisa e Busca
                    - **Teste de Pesquisa**: Interface simples para testar consultas
                    - **Busca Semântica**: Busca avançada com IA para encontrar itens similares
                    - **Configurações Flexíveis**: Ajuste do número de resultados
                    
                    ### 📊 Análise e Relatórios
                    - **Análise de Dados**: Visualização e análise de dados de orçamento
                    - **Relatórios**: Geração de relatórios detalhados
                    - **Exportação**: Dados em CSV e Excel
                    
                    ### ⚙️ Configurações
                    - **Configurações do Sistema**: Ajustes de API, timeout e preferências
                    - **Testes de Conectividade**: Verificação do status da API
                    - **Informações do Sistema**: Detalhes técnicos e versões
                    
                    ## 🏗️ Arquitetura
                    
                    O sistema utiliza uma arquitetura modular com:
                    - **Frontend**: Interface Gradio responsiva e intuitiva
                    - **Backend**: API FastAPI para processamento de dados
                    - **IA**: Modelos de embedding para busca semântica
                    - **Dados**: Base de dados de itens de construção civil
                    
                    ## 🚀 Como Usar
                    
                    1. **Inicie o Backend**: Use a aba "Controle do Sistema" para iniciar o servidor
                    2. **Teste a Conexão**: Verifique se tudo está funcionando na aba "Teste de Pesquisa"
                    3. **Explore as Funcionalidades**: Use as diferentes abas conforme sua necessidade
                    4. **Configure**: Ajuste as configurações na aba "Configurações" se necessário
                    
                    ## 📝 Versão
                     - **Sistema**: v2.0 - Versão Modular Integrada
                     - **Gradio**: {}
                     - **Python**: {}
                     """.format(gr.__version__, sys.version.split()[0])
                )
        
        # Funções para controle dos agentes
        def load_agent_config(agent_name):
            """Carrega a configuração do agente selecionado"""
            try:
                config_path = app_dir / "agents_config.json"
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    agent_config = config.get('agents', {}).get(agent_name, {})
                    base_prompt = agent_config.get('base_prompt', '')
                    
                    # Carrega prioridades do projeto se existirem
                    project_priorities = config.get('project_priorities', {})
                    project_profile = ', '.join(project_priorities.keys()) if project_priorities else ''
                    
                    return base_prompt, project_profile, f"✅ Configuração do agente '{agent_name}' carregada com sucesso"
                else:
                    return "", "", "⚠️ Arquivo agents_config.json não encontrado"
            except Exception as e:
                return "", "", f"❌ Erro ao carregar configuração: {str(e)}"
        
        def save_agent_config(agent_name, base_prompt, project_profile):
            """Salva a configuração do agente"""
            try:
                config_path = app_dir / "agents_config.json"
                
                # Carrega configuração existente ou cria nova
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                else:
                    config = {"agents": {}, "project_priorities": {}}
                
                # Atualiza configuração do agente
                if 'agents' not in config:
                    config['agents'] = {}
                
                config['agents'][agent_name] = {
                    "model": config['agents'].get(agent_name, {}).get('model', 'gpt-4o-mini'),
                    "base_prompt": base_prompt
                }
                
                # Atualiza prioridades do projeto
                if project_profile.strip():
                    profiles = [p.strip() for p in project_profile.split(',') if p.strip()]
                    for i, profile in enumerate(profiles):
                        config['project_priorities'][profile] = 1.0 + (0.1 * i)
                
                # Salva arquivo
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                return f"✅ Configuração do agente '{agent_name}' salva com sucesso"
            except Exception as e:
                return f"❌ Erro ao salvar configuração: {str(e)}"
        
        def reset_agent_config(agent_name):
            """Reseta a configuração do agente para valores padrão"""
            defaults = {
                "classifier": "Você é um classificador especializado em construção civil. Analise o texto e classifique adequadamente.",
                "reasoner": "Você é um engenheiro de especificações sênior e detalhista. Sua tarefa é analisar a solicitação de um usuário e escolher o serviço mais adequado de uma lista de candidatos.",
                "finder": "Sistema de busca híbrida para itens de construção civil."
            }
            
            base_prompt = defaults.get(agent_name, "")
            return base_prompt, "", f"🔄 Configuração do agente '{agent_name}' resetada para valores padrão"
        
        def test_agent_with_config(agent_name, query, user_guidance, project_profile):
            """Testa o agente com a configuração atual"""
            if not query.strip():
                return {"erro": "Digite uma query para testar"}, {}, "❌ Query de teste vazia"
            
            try:
                # Verifica se o backend está rodando
                try:
                    health_response = requests.get("http://127.0.0.1:8001/health", timeout=2)
                    if health_response.status_code != 200:
                        return {"erro": "Backend não está respondendo"}, {}, "❌ Backend offline"
                except:
                    return {"erro": "Backend não está acessível"}, {}, "❌ Erro de conexão com backend"
                
                # Prepara dados para teste
                test_data = {
                    "texto_busca": query,
                    "top_k": 3
                }
                
                # Adiciona orientação e perfil se fornecidos
                if user_guidance.strip():
                    test_data["user_guidance"] = user_guidance.strip()
                if project_profile.strip():
                    test_data["project_profile"] = project_profile.strip()
                
                # Realiza o teste
                response = requests.post(
                    "http://127.0.0.1:8001/buscar",
                    json=test_data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    results = response.json()
                    trace = results.get('trace', {})
                    
                    # Remove trace dos resultados principais para melhor visualização
                    clean_results = {k: v for k, v in results.items() if k != 'trace'}
                    
                    audit_msg = f"✅ Teste realizado com sucesso\nAgente: {agent_name}\nQuery: {query}\nResultados: {len(clean_results.get('resultados', []))} itens"
                    
                    return clean_results, trace, audit_msg
                else:
                    error_msg = f"Erro {response.status_code}: {response.text}"
                    return {"erro": error_msg}, {}, f"❌ Erro no teste: {response.status_code}"
                    
            except requests.exceptions.Timeout:
                return {"erro": "Timeout no teste"}, {}, "⏱️ Teste demorou muito para responder"
            except Exception as e:
                return {"erro": f"Erro inesperado: {str(e)}"}, {}, f"❌ Erro: {str(e)}"
        
        # Funções dos botões
        def update_status():
            status, _ = controller.check_backend_status()
            return status
        
        def start_backend_action():
            result = controller.start_backend()
            status, _ = controller.check_backend_status()
            return status, result
        
        def stop_backend_action():
            result = controller.stop_backend()
            status, _ = controller.check_backend_status()
            return status, result
        
        def restart_backend_action():
            result = controller.restart_backend()
            status, _ = controller.check_backend_status()
            return status, result
        
        # Função de pesquisa
        def perform_search(query, num_results):
            """Realiza pesquisa no backend"""
            if not query.strip():
                return {"erro": "Digite um texto para pesquisar"}, "❌ Texto de pesquisa vazio"
            
            try:
                import requests
                import json
                
                # Verifica se o backend está rodando
                try:
                    health_response = requests.get("http://127.0.0.1:8001/health", timeout=2)
                    if health_response.status_code != 200:
                        return {"erro": "Backend não está respondendo"}, "❌ Backend offline"
                except:
                    return {"erro": "Backend não está acessível"}, "❌ Erro de conexão com backend"
                
                # Realiza a pesquisa
                search_data = {
                    "texto_busca": query,
                    "top_k": int(num_results)
                }
                
                response = requests.post(
                    "http://127.0.0.1:8001/buscar",
                    json=search_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json()
                    status_msg = f"✅ Pesquisa realizada com sucesso! Encontrados {len(results.get('resultados', []))} resultados"
                    return results, status_msg
                else:
                    error_msg = f"Erro {response.status_code}: {response.text}"
                    return {"erro": error_msg}, f"❌ Erro na pesquisa: {response.status_code}"
                    
            except requests.exceptions.Timeout:
                return {"erro": "Timeout na pesquisa"}, "⏱️ Pesquisa demorou muito para responder"
            except Exception as e:
                return {"erro": f"Erro inesperado: {str(e)}"}, f"❌ Erro: {str(e)}"
        
        def restart_interface():
            """Reinicia a interface do painel"""
            import time
            time.sleep(1)
            # Força o recarregamento da página
            return gr.update(), "🔄 Interface reiniciada! Recarregue a página se necessário."
        
        # Conectar eventos
        refresh_btn.click(
            fn=update_status,
            outputs=[status_display]
        )
        
        start_btn.click(
            fn=start_backend_action,
            outputs=[status_display, action_log]
        )
        
        stop_btn.click(
            fn=stop_backend_action,
            outputs=[status_display, action_log]
        )
        
        restart_btn.click(
            fn=restart_backend_action,
            outputs=[status_display, action_log]
        )
        
        # Função de pesquisa
        search_btn.click(
            fn=perform_search,
            inputs=[search_input, top_k],
            outputs=[search_results, search_status]
        )
        
        # Pesquisa ao pressionar Enter
        search_input.submit(
            fn=perform_search,
            inputs=[search_input, top_k],
            outputs=[search_results, search_status]
        )
        
        # Reiniciar interface
        restart_interface_btn.click(
            fn=restart_interface,
            outputs=[status_display, action_log]
        )
        
        # Event handlers para controle dos agentes
        agent_selector.change(
            fn=load_agent_config,
            inputs=[agent_selector],
            outputs=[base_prompt_editor, project_profile_editor, config_status]
        )
        
        load_config_btn.click(
            fn=load_agent_config,
            inputs=[agent_selector],
            outputs=[base_prompt_editor, project_profile_editor, config_status]
        )
        
        save_config_btn.click(
            fn=save_agent_config,
            inputs=[agent_selector, base_prompt_editor, project_profile_editor],
            outputs=[config_status]
        )
        
        reset_config_btn.click(
            fn=reset_agent_config,
            inputs=[agent_selector],
            outputs=[base_prompt_editor, project_profile_editor, config_status]
        )
        
        test_agent_btn.click(
            fn=test_agent_with_config,
            inputs=[agent_selector, test_query, user_guidance_editor, project_profile_editor],
            outputs=[test_results, trace_display, audit_log]
        )
        
        # Teste ao pressionar Enter no campo de query
        test_query.submit(
            fn=test_agent_with_config,
            inputs=[agent_selector, test_query, user_guidance_editor, project_profile_editor],
            outputs=[test_results, trace_display, audit_log]
        )
        
        # Atualização inicial do status
        demo.load(
            fn=update_status,
            outputs=[status_display]
        )
        
        # Carrega configuração inicial do agente padrão
        demo.load(
            fn=lambda: load_agent_config("reasoner"),
            outputs=[base_prompt_editor, project_profile_editor, config_status]
        )
    
    return demo

def main():
    """Função principal"""
    print("=" * 60)
    print("PAINEL DE CONTROLE - SISTEMA DE ORÇAMENTO")
    print("=" * 60)
    print()
    
    # Verifica se os arquivos necessários existem
    arquivos_necessarios = [
        "backend/app/main.py",
        "backend/services/finder.py"
    ]
    
    for arquivo in arquivos_necessarios:
        if not (app_dir / arquivo).exists():
            print(f"❌ Arquivo necessário não encontrado: {arquivo}")
            input("Pressione Enter para sair...")
            sys.exit(1)
    
    print("✅ Todos os arquivos necessários encontrados")
    print("🚀 Iniciando painel de controle...")
    print()
    
    # Cria e executa o dashboard
    dashboard = create_dashboard()
    
    try:
        dashboard.launch(
            server_name="127.0.0.1",
            server_port=7861,
            share=False,
            show_error=True,
            quiet=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Painel encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()