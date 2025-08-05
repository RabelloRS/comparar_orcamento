#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de inicialização da aplicação de orçamento de obras.
Este script facilita o processo de iniciar tanto o backend quanto o frontend.
"""

import subprocess
import sys
import time
import os
import threading
from pathlib import Path

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas."""
    print("🔍 Verificando dependências...")
    
    try:
        import streamlit
        import fastapi
        import uvicorn
        import pandas
        import requests
        print("✅ Todas as dependências principais estão instaladas.")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r requirements.txt")
        return False

def verificar_arquivos():
    """Verifica se os arquivos necessários existem."""
    print("📁 Verificando arquivos necessários...")
    
    arquivos_necessarios = [
        "interface.py",
        "app/main.py",
        "dados/banco_dados_servicos.txt",
        "requirements.txt"
    ]
    
    arquivos_faltando = []
    for arquivo in arquivos_necessarios:
        if not os.path.exists(arquivo):
            arquivos_faltando.append(arquivo)
    
    if arquivos_faltando:
        print(f"❌ Arquivos faltando: {', '.join(arquivos_faltando)}")
        return False
    
    print("✅ Todos os arquivos necessários estão presentes.")
    return True

def iniciar_backend():
    """Inicia o servidor backend FastAPI."""
    print("🚀 Iniciando backend...")
    
    try:
        # Muda para o diretório app
        os.chdir("app")
        
        # Inicia o servidor uvicorn
        processo = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--reload", 
            "--port", "8000",
            "--host", "localhost"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Volta para o diretório raiz
        os.chdir("..")
        
        return processo
        
    except Exception as e:
        print(f"❌ Erro ao iniciar backend: {e}")
        return None

def aguardar_backend():
    """Aguarda o backend ficar disponível."""
    print("⏳ Aguardando backend ficar disponível...")
    
    import requests
    
    for tentativa in range(30):  # Tenta por 30 segundos
        try:
            response = requests.get("http://localhost:8000/", timeout=1)
            if response.status_code == 200:
                print("✅ Backend está funcionando!")
                return True
        except:
            pass
        
        time.sleep(1)
        print(f"   Tentativa {tentativa + 1}/30...")
    
    print("❌ Backend não ficou disponível em 30 segundos.")
    return False

def iniciar_frontend():
    """Inicia a interface Streamlit."""
    print("🎨 Iniciando interface...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", 
            "run", "interface.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Interface encerrada pelo usuário.")
    except Exception as e:
        print(f"❌ Erro ao iniciar interface: {e}")

def main():
    """Função principal."""
    print("="*60)
    print("🏗️  ASSISTENTE DE ORÇAMENTO DE OBRAS PÚBLICAS")
    print("="*60)
    
    # Verifica dependências
    if not verificar_dependencias():
        return
    
    # Verifica arquivos
    if not verificar_arquivos():
        return
    
    print("\n🎯 Escolha uma opção:")
    print("1. Iniciar aplicação completa (backend + frontend)")
    print("2. Iniciar apenas o backend")
    print("3. Iniciar apenas o frontend")
    print("4. Sair")
    
    escolha = input("\nDigite sua escolha (1-4): ").strip()
    
    if escolha == "1":
        print("\n🚀 Iniciando aplicação completa...")
        
        # Inicia backend em thread separada
        processo_backend = iniciar_backend()
        if not processo_backend:
            return
        
        # Aguarda backend ficar disponível
        if not aguardar_backend():
            processo_backend.terminate()
            return
        
        print("\n🎉 Backend iniciado com sucesso!")
        print("📱 Abrindo interface...")
        
        try:
            # Inicia frontend
            iniciar_frontend()
        finally:
            print("\n🛑 Encerrando backend...")
            processo_backend.terminate()
            processo_backend.wait()
    
    elif escolha == "2":
        print("\n🚀 Iniciando apenas o backend...")
        processo_backend = iniciar_backend()
        if processo_backend:
            try:
                print("✅ Backend rodando. Pressione Ctrl+C para parar.")
                processo_backend.wait()
            except KeyboardInterrupt:
                print("\n🛑 Encerrando backend...")
                processo_backend.terminate()
    
    elif escolha == "3":
        print("\n🎨 Iniciando apenas o frontend...")
        print("⚠️  Certifique-se de que o backend está rodando em http://localhost:8000")
        iniciar_frontend()
    
    elif escolha == "4":
        print("👋 Até logo!")
    
    else:
        print("❌ Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()