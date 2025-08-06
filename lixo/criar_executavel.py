#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar executável da aplicação de orçamento
Este script empacota a aplicação completa em um executável standalone
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def verificar_pyinstaller():
    """Verifica se PyInstaller está instalado"""
    try:
        import PyInstaller
        print("✅ PyInstaller encontrado")
        return True
    except ImportError:
        print("❌ PyInstaller não encontrado")
        print("Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller instalado com sucesso")
            return True
        except subprocess.CalledProcessError:
            print("❌ Erro ao instalar PyInstaller")
            return False

def criar_script_principal():
    """Cria o script principal que será empacotado"""
    script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal do executável - Aplicação de Orçamento
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser
from pathlib import Path

# Adiciona o diretório da aplicação ao path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(app_dir / "app"))

def iniciar_backend():
    """Inicia o servidor FastAPI"""
    try:
        import uvicorn
        from app.main import app
        
        print("🚀 Iniciando servidor backend...")
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        print(f"❌ Erro ao iniciar backend: {e}")
        input("Pressione Enter para sair...")
        sys.exit(1)

def iniciar_frontend():
    """Inicia a interface Streamlit"""
    try:
        time.sleep(3)  # Aguarda o backend iniciar
        
        # Comando para iniciar streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "interface.py", "--server.port=8501"]
        
        print("🎨 Iniciando interface frontend...")
        subprocess.run(cmd, cwd=app_dir)
    except Exception as e:
        print(f"❌ Erro ao iniciar frontend: {e}")
        input("Pressione Enter para sair...")
        sys.exit(1)

def main():
    """Função principal"""
    print("="*60)
    print("🏗️  SISTEMA DE ORÇAMENTO - CONSTRUÇÃO CIVIL")
    print("="*60)
    print()
    
    # Verifica se os arquivos necessários existem
    arquivos_necessarios = [
        "dados/banco_dados_servicos.txt",
        "interface.py",
        "app/main.py"
    ]
    
    for arquivo in arquivos_necessarios:
        if not (app_dir / arquivo).exists():
            print(f"❌ Arquivo necessário não encontrado: {arquivo}")
            input("Pressione Enter para sair...")
            sys.exit(1)
    
    print("✅ Todos os arquivos necessários encontrados")
    print()
    
    try:
        # Inicia o backend em uma thread separada
        backend_thread = threading.Thread(target=iniciar_backend, daemon=True)
        backend_thread.start()
        
        print("⏳ Aguardando backend inicializar...")
        time.sleep(5)
        
        # Abre o navegador automaticamente
        print("🌐 Abrindo navegador...")
        webbrowser.open("http://localhost:8501")
        
        # Inicia o frontend (processo principal)
        iniciar_frontend()
        
    except KeyboardInterrupt:
        print("\n👋 Aplicação encerrada pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()
'''
    
    with open("app_principal.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ Script principal criado: app_principal.py")

def criar_spec_file():
    """Cria o arquivo .spec para PyInstaller"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app_principal.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('dados', 'dados'),
        ('app', 'app'),
        ('interface.py', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'uvicorn',
        'fastapi',
        'pandas',
        'torch',
        'sentence_transformers',
        'sklearn',
        'numpy',
        'requests',
        'openpyxl',
        'xlsxwriter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SistemaOrcamento',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icone.ico' if os.path.exists('icone.ico') else None,
)
'''
    
    with open("app.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("✅ Arquivo .spec criado: app.spec")

def criar_executavel():
    """Cria o executável usando PyInstaller"""
    print("🔨 Criando executável...")
    print("⚠️  Este processo pode demorar alguns minutos...")
    
    try:
        # Comando PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--onefile",
            "--name=SistemaOrcamento",
            "--add-data=dados;dados",
            "--add-data=app;app",
            "--add-data=interface.py;.",
            "--hidden-import=streamlit",
            "--hidden-import=uvicorn",
            "--hidden-import=fastapi",
            "--hidden-import=pandas",
            "--hidden-import=torch",
            "--hidden-import=sentence_transformers",
            "--hidden-import=sklearn",
            "--hidden-import=numpy",
            "--hidden-import=requests",
            "--hidden-import=openpyxl",
            "--hidden-import=xlsxwriter",
            "app_principal.py"
        ]
        
        resultado = subprocess.run(cmd, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print("✅ Executável criado com sucesso!")
            print("📁 Localização: dist/SistemaOrcamento.exe")
            return True
        else:
            print("❌ Erro ao criar executável:")
            print(resultado.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def criar_readme_executavel():
    """Cria um README para o executável"""
    readme_content = '''# Sistema de Orçamento - Executável

## Como usar o executável

1. **Baixe o arquivo**: `SistemaOrcamento.exe`

2. **Execute**: Clique duas vezes no arquivo `.exe`

3. **Aguarde**: O sistema irá:
   - Inicializar o backend (API)
   - Abrir automaticamente o navegador
   - Carregar a interface web

4. **Use a aplicação**: A interface estará disponível em `http://localhost:8501`

## Requisitos do Sistema

- **Sistema Operacional**: Windows 10 ou superior
- **Memória RAM**: Mínimo 4GB (recomendado 8GB)
- **Espaço em Disco**: Aproximadamente 500MB livres
- **Conexão com Internet**: Necessária para algumas funcionalidades

## Funcionalidades

- ✅ **Busca Semântica**: Pesquisa inteligente de serviços
- ✅ **Filtro em Tempo Real**: Busca rápida no banco de dados
- ✅ **Processamento em Lote**: Upload e análise de planilhas Excel
- ✅ **Interface Intuitiva**: Fácil de usar

## Solução de Problemas

### O executável não inicia
- Verifique se tem permissões de administrador
- Desative temporariamente o antivírus
- Execute como administrador

### Erro de "Porta em uso"
- Feche outras aplicações que possam usar as portas 8000 ou 8501
- Reinicie o computador se necessário

### Interface não carrega
- Aguarde alguns segundos para o sistema inicializar completamente
- Verifique se o navegador não está bloqueando localhost
- Tente acessar manualmente: http://localhost:8501

## Suporte

Em caso de problemas, verifique:
1. Se todos os arquivos estão na mesma pasta
2. Se tem conexão com internet
3. Se o Windows Defender não está bloqueando

---
**Versão**: 1.0  
**Data**: 2024
'''
    
    with open("README_EXECUTAVEL.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ README criado: README_EXECUTAVEL.md")

def main():
    """Função principal"""
    print("🚀 CRIADOR DE EXECUTÁVEL - Sistema de Orçamento")
    print("="*60)
    print()
    
    # Verifica se estamos no diretório correto
    if not os.path.exists("interface.py"):
        print("❌ Execute este script na pasta raiz do projeto")
        return
    
    # Verifica e instala PyInstaller
    if not verificar_pyinstaller():
        return
    
    print()
    print("📋 Preparando arquivos...")
    
    # Cria os arquivos necessários
    criar_script_principal()
    criar_spec_file()
    criar_readme_executavel()
    
    print()
    resposta = input("🤔 Deseja criar o executável agora? (s/n): ")
    
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        print()
        if criar_executavel():
            print()
            print("🎉 SUCESSO! Executável criado com sucesso!")
            print()
            print("📁 Arquivos gerados:")
            print("   - dist/SistemaOrcamento.exe (EXECUTÁVEL PRINCIPAL)")
            print("   - README_EXECUTAVEL.md (instruções)")
            print()
            print("💡 Dicas:")
            print("   1. Teste o executável antes de distribuir")
            print("   2. Inclua o README junto com o executável")
            print("   3. O executável é standalone (não precisa de Python)")
            print()
        else:
            print("❌ Falha ao criar executável")
    else:
        print("ℹ️  Arquivos preparados. Execute novamente quando quiser criar o executável.")

if __name__ == "__main__":
    main()