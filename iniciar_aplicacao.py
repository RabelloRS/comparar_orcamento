#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de inicialização da aplicação de orçamento de obras.
Este script inicia automaticamente o backend e o frontend.
"""

import subprocess
import sys
import time
import os
import threading
import webbrowser
import requests

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas."""
    print("Verificando dependências...")
    try:
        import streamlit, fastapi, uvicorn, pandas, requests
        print("Todas as dependências principais estão instaladas.")
        return True
    except ImportError as e:
        print(f"Dependência faltando: {e.name}")
        print("Por favor, execute: pip install -r requirements.txt")
        return False

def verificar_arquivos():
    """Verifica se os arquivos necessários existem."""
    print("Verificando arquivos necessários...")
    arquivos_necessarios = [
        "interface.py",
        "app/main.py",
        "dados/banco_dados_servicos.txt",
        "requirements.txt"
    ]
    arquivos_faltando = [arq for arq in arquivos_necessarios if not os.path.exists(arq)]
    if arquivos_faltando:
        print(f"Arquivos faltando: {', '.join(arquivos_faltando)}")
        return False
    print("Todos os arquivos necessários estão presentes.")
    return True

def iniciar_backend():
    """Inicia o servidor backend FastAPI e captura seus logs."""
    print("Iniciando backend (FastAPI + Uvicorn)...")
    comando = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ]

    processo = subprocess.Popen(
        comando, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        encoding='utf-8',
        errors='replace'
    )

    def log_output(pipe, prefix):
        try:
            for line in iter(pipe.readline, ''):
                print(f"[{prefix}] {line.strip()}")
            pipe.close()
        except Exception as e:
            print(f"[log_thread_error] {e}")

    threading.Thread(target=log_output, args=(processo.stdout, 'BACKEND_OUT'), daemon=True).start()
    threading.Thread(target=log_output, args=(processo.stderr, 'BACKEND_ERR'), daemon=True).start()

    return processo

def aguardar_backend():
    """Aguarda o backend ficar disponível."""
    print("Aguardando o backend ficar totalmente operacional...")
    print("   (Pode levar até 120 segundos na primeira vez)")
    for i in range(120):
        try:
            response = requests.get("http://127.0.0.1:8000/", timeout=2)
            if response.status_code == 200:
                print("Backend está funcionando!")
                return True
        except requests.ConnectionError:
            time.sleep(1)
        if (i + 1) % 10 == 0:
            print(f"   ... {i+1} segundos se passaram.")
    print("O backend não respondeu a tempo.")
    return False

def iniciar_frontend():
    """Inicia a interface Streamlit."""
    print("Iniciando interface (Streamlit)...")
    comando = [
        sys.executable, "-m", "streamlit", 
        "run", "interface.py",
        "--server.port", "8501",
        "--server.address", "127.0.0.1",
        "--browser.gatherUsageStats", "false"
    ]
    # Usar CREATE_NO_WINDOW no Windows para não abrir um console
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    subprocess.Popen(comando, creationflags=flags)
    print("Interface iniciada.")

def abrir_navegador():
    """Abre o navegador na página da aplicação."""
    time.sleep(4) # Dá um tempo para o Streamlit iniciar
    url = "http://127.0.0.1:8501"
    print(f"Abrindo {url} no seu navegador...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Não foi possível abrir o navegador: {e}")
        print(f"   Por favor, acesse manualmente: {url}")

def main():
    """Função principal para orquestrar a inicialização."""
    print("="*60)
    print("INICIALIZADOR AUTOMÁTICO DO ASSISTENTE DE ORÇAMENTO")
    print("="*60)

    if not verificar_dependencias() or not verificar_arquivos():
        input("Pressione Enter para sair.")
        return

    processo_backend = None
    try:
        processo_backend = iniciar_backend()
        if aguardar_backend():
            iniciar_frontend()
            abrir_navegador()
            print("\nAplicação iniciada com sucesso!")
            print("   O backend e o frontend estão rodando em segundo plano.")
            print("   Feche esta janela para encerrar a aplicação.")
            processo_backend.wait() # Mantém o script rodando
        else:
            print("\nFalha ao iniciar o backend. A aplicação não pode continuar.")
    except KeyboardInterrupt:
        print("\nAplicação encerrada pelo usuário.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
    finally:
        if processo_backend:
            print("Encerrando processo do backend...")
            processo_backend.terminate()
            processo_backend.wait()
        print("Até logo!")

if __name__ == "__main__":
    main()