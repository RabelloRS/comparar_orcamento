import os
import sys
import time
import threading
import subprocess
import webbrowser
from pathlib import Path

# Adiciona o diretorio da aplicacao ao path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(app_dir / "app"))

def iniciar_backend():
    """Inicia o servidor FastAPI"""
    try:
        import uvicorn
        from app.main import app
        
        print("Iniciando servidor backend...")
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        print(f"Erro ao iniciar backend: {e}")
        input("Pressione Enter para sair...")
        sys.exit(1)

def iniciar_frontend():
    """Inicia a interface Streamlit"""
    try:
        time.sleep(3)  # Aguarda o backend iniciar
        
        # Comando para iniciar a nova interface Gradio
        # cmd = [sys.executable, "-m", "streamlit", "run", "interface.py", "--server.port=8501"] # Linha antiga comentada
        cmd = [sys.executable, "interface_gradio.py"]
        
        print("Iniciando interface frontend...")
        subprocess.run(cmd, cwd=app_dir)
    except Exception as e:
        print(f"Erro ao iniciar frontend: {e}")
        input("Pressione Enter para sair...")
        sys.exit(1)

def main():
    """Funcao principal"""
    print("=" * 60)
    print("SISTEMA DE ORCAMENTO - CONSTRUCAO CIVIL")
    print("=" * 60)
    print()
    
    # Verifica se os arquivos necessarios existem
    arquivos_necessarios = [
        "dados/banco_dados_servicos.txt",
        "interface_gradio.py",
        "app/main.py"
    ]
    
    for arquivo in arquivos_necessarios:
        if not (app_dir / arquivo).exists():
            print(f"Arquivo necessario nao encontrado: {arquivo}")
            input("Pressione Enter para sair...")
            sys.exit(1)
    
    print("Todos os arquivos necessarios encontrados")
    print()
    
    try:
        # Inicia o backend em uma thread separada
        backend_thread = threading.Thread(target=iniciar_backend, daemon=True)
        backend_thread.start()
        
        print("Aguardando backend inicializar...")
        time.sleep(5)
        
        # Abre o navegador automaticamente
        print("Abrindo navegador...")
        webbrowser.open("http://localhost:7860")
        
        # Inicia o frontend (processo principal)
        iniciar_frontend()
        
    except KeyboardInterrupt:
        print("\nAplicacao encerrada pelo usuario")
    except Exception as e:
        print(f"Erro inesperado: {e}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()