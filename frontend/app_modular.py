import gradio as gr
import sys
import os

# Adiciona o diretório pages ao path para importar as páginas
sys.path.append(os.path.join(os.path.dirname(__file__), 'pages'))

# Importa as páginas modulares
try:
    from busca_semantica import busca_page
    from analise_dados import analise_page
    from configuracoes import config_page
except ImportError as e:
    print(f"Erro ao importar páginas: {e}")
    print("Certifique-se de que os arquivos estão no diretório 'pages/'")
    sys.exit(1)

def criar_cabecalho():
    """Cria o cabeçalho da aplicação."""
    return gr.Markdown("""
    # 🏗️ Sistema de Orçamento de Obras - Versão Modular
    
    **Assistente Inteligente para Orçamento de Obras Públicas**
    
    ---
    """)

def criar_rodape():
    """Cria o rodapé da aplicação."""
    return gr.Markdown("""
    ---
    
    <div style="text-align: center; color: #666; font-size: 0.9em; margin-top: 20px;">
        💡 <strong>Dica:</strong> Cada aba pode ser desenvolvida e testada independentemente.<br>
        🔧 Desenvolvido com Gradio | 📊 Sistema Modular de IA
    </div>
    """)

# --- Aplicação Principal Modular ---
with gr.Blocks(
    theme=gr.themes.Soft(),
    title="Sistema de Orçamento - Modular",
    css="""
    .gradio-container {
        max-width: 1200px !important;
    }
    .tab-nav {
        background: linear-gradient(90deg, #f0f2f6, #ffffff);
        border-radius: 10px;
        padding: 5px;
    }
    """
) as demo:
    
    # Cabeçalho
    criar_cabecalho()
    
    # Navegação principal por abas
    with gr.Tabs(elem_classes=["tab-nav"]) as main_tabs:
        
        # Aba 1: Busca Semântica
        with gr.TabItem("🔍 Busca Semântica", elem_id="busca-tab"):
            busca_page.render()
        
        # Aba 2: Análise de Dados
        with gr.TabItem("📈 Análise de Dados", elem_id="analise-tab"):
            analise_page.render()
        
        # Aba 3: Configurações
        with gr.TabItem("⚙️ Configurações", elem_id="config-tab"):
            config_page.render()
        
        # Aba 4: Sobre o Sistema
        with gr.TabItem("ℹ️ Sobre", elem_id="sobre-tab"):
            gr.Markdown("""
            ## 📋 Sobre o Sistema Modular
            
            ### 🎯 Objetivo
            Este sistema demonstra como organizar uma aplicação Gradio grande em módulos separados,
            facilitando a manutenção e o desenvolvimento colaborativo.
            
            ### 🏗️ Arquitetura Modular
            
            ```
            frontend/
            ├── app_modular.py          # Arquivo principal (este arquivo)
            ├── pages/                  # Diretório das páginas
            │   ├── busca_semantica.py  # Página de busca
            │   ├── analise_dados.py    # Página de análise
            │   └── configuracoes.py    # Página de configurações
            └── interface_gradio.py     # Interface original (monolítica)
            ```
            
            ### ✨ Vantagens da Abordagem Modular
            
            #### 🔧 **Desenvolvimento**
            - **Separação de responsabilidades:** Cada página tem sua própria lógica
            - **Desenvolvimento paralelo:** Equipes podem trabalhar em páginas diferentes
            - **Testes independentes:** Cada página pode ser testada isoladamente
            - **Reutilização:** Páginas podem ser reutilizadas em outros projetos
            
            #### 📦 **Manutenção**
            - **Código organizado:** Funcionalidades relacionadas ficam juntas
            - **Debugging facilitado:** Problemas são isolados por página
            - **Atualizações seguras:** Mudanças em uma página não afetam outras
            - **Versionamento granular:** Controle de versão por funcionalidade
            
            #### 🚀 **Performance**
            - **Carregamento otimizado:** Apenas o necessário é carregado
            - **Memória eficiente:** Recursos são compartilhados entre páginas
            - **Escalabilidade:** Fácil adição de novas funcionalidades
            
            ### 🛠️ Como Adicionar uma Nova Página
            
            1. **Crie o arquivo da página:**
            ```python
            # frontend/pages/nova_pagina.py
            import gradio as gr
            
            with gr.Blocks() as nova_page:
                gr.Markdown("## Minha Nova Página")
                # Seus componentes aqui...
            
            if __name__ == "__main__":
                nova_page.launch()  # Para testes independentes
            ```
            
            2. **Importe no arquivo principal:**
            ```python
            # frontend/app_modular.py
            from nova_pagina import nova_page
            ```
            
            3. **Adicione a aba:**
            ```python
            with gr.TabItem("🆕 Nova Página"):
                nova_page.render()
            ```
            
            ### 🔄 Alternativas de Navegação
            
            #### **Páginas com URLs (Multipage)**
            ```python
            with gr.Blocks() as demo:
                # Página principal
                busca_page.render()
            
            with demo.route("Análise", "/analise"):
                analise_page.render()
            
            with demo.route("Config", "/config"):
                config_page.render()
            ```
            
            #### **Interface Tabular (TabbedInterface)**
            ```python
            demo = gr.TabbedInterface(
                [busca_page, analise_page, config_page],
                ["Busca", "Análise", "Configurações"]
            )
            ```
            
            ### 📚 Recursos Utilizados
            
            - **Gradio Blocks:** Container principal para layouts complexos
            - **Método .render():** Renderiza páginas dentro de outras páginas
            - **Tabs:** Navegação por abas dentro da mesma página
            - **CSS Personalizado:** Estilização da interface
            - **State Management:** Compartilhamento de estado entre componentes
            
            ### 🎨 Personalização de Tema
            
            O sistema usa o tema `Soft` do Gradio com CSS personalizado para:
            - Layout responsivo (max-width: 1200px)
            - Estilização das abas com gradiente
            - Espaçamento otimizado
            
            ### 🔗 Links Úteis
            
            - [Documentação do Gradio](https://gradio.app/docs/)
            - [Guia de Blocks](https://gradio.app/guides/blocks-and-event-listeners/)
            - [Aplicações Multipáginas](https://gradio.app/guides/multipage-apps/)
            - [Temas e CSS](https://gradio.app/guides/theming-guide/)
            
            ---
            
            **💡 Dica:** Execute cada página individualmente com `python pages/nome_da_pagina.py` 
            para desenvolvimento e testes isolados!
            """)
    
    # Rodapé
    criar_rodape()

if __name__ == "__main__":
    print("🚀 Iniciando Sistema de Orçamento - Versão Modular")
    print("📁 Páginas carregadas:")
    print("   🔍 Busca Semântica")
    print("   📈 Análise de Dados")
    print("   ⚙️ Configurações")
    print("   ℹ️ Sobre o Sistema")
    print("\n💡 Para testar páginas individualmente:")
    print("   python pages/busca_semantica.py")
    print("   python pages/analise_dados.py")
    print("   python pages/configuracoes.py")
    print("\n🌐 Iniciando servidor...")
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7862,
        share=False,
        show_error=True
    )