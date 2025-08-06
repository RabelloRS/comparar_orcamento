#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste do Sistema de Logs
Testa todas as funcionalidades de logging implementadas no sistema.
"""

import sys
import time
from pathlib import Path

# Adiciona o diretório utils ao path
sys.path.insert(0, str(Path(__file__).parent / "utils"))

try:
    from logger import (
        log_search, log_search_results, log_search_error,
        log_analysis, log_config, log_backend, log_api,
        log_system, log_error, log_performance
    )
except ImportError as e:
    print(f"Erro ao importar logger: {e}")
    sys.exit(1)

def teste_logs_busca_semantica():
    """Testa logs da busca semântica"""
    print("🔍 Testando logs de Busca Semântica...")
    
    # Simula uma busca
    log_search("parede de gesso", 10, "127.0.0.1")
    time.sleep(0.1)
    
    # Simula resultados
    log_search_results("parede de gesso", 5, 0.234)
    time.sleep(0.1)
    
    # Simula erro
    log_search_error("busca inválida", "Erro de conexão com API")
    
def teste_logs_analise_dados():
    """Testa logs da análise de dados"""
    print("📊 Testando logs de Análise de Dados...")
    
    # Simula upload de arquivo
    log_analysis("Upload", "dados_orcamento.csv", 1500)
    time.sleep(0.1)
    
    # Simula geração de relatório
    log_analysis("Relatório", records=1500)
    time.sleep(0.1)
    
    # Simula exportação
    log_analysis("Exportação", "relatorio_final.xlsx", 1500)
    
def teste_logs_configuracoes():
    """Testa logs de configurações"""
    print("⚙️ Testando logs de Configurações...")
    
    # Simula mudança de configuração
    log_config("API_URL", "http://localhost:8000", "http://127.0.0.1:8000", "127.0.0.1")
    time.sleep(0.1)
    
    # Simula mudança de timeout
    log_config("TIMEOUT", "30", "60")
    
def teste_logs_backend():
    """Testa logs do backend"""
    print("🖥️ Testando logs de Backend...")
    
    # Simula operações do backend
    log_backend("Start", "Iniciando processo do backend")
    time.sleep(0.1)
    
    log_backend("Status Check", "Online")
    time.sleep(0.1)
    
    log_backend("Stop", "Backend parado com sucesso")
    
def teste_logs_api():
    """Testa logs de API"""
    print("🌐 Testando logs de API...")
    
    # Simula requisições de API
    log_api("/health", "GET", 200, 0.045, "127.0.0.1")
    time.sleep(0.1)
    
    log_api("/search", "POST", 200, 0.234)
    time.sleep(0.1)
    
    log_api("/upload", "POST", 500, 1.234)
    
def teste_logs_sistema():
    """Testa logs do sistema"""
    print("🖥️ Testando logs de Sistema...")
    
    # Simula eventos do sistema
    log_system("Startup", "Sistema iniciado com sucesso")
    time.sleep(0.1)
    
    log_system("System Info", '{"cpu_percent": 45.2, "memory_percent": 67.8, "disk_percent": 23.1}')
    
def teste_logs_erro():
    """Testa logs de erro"""
    print("❌ Testando logs de Erro...")
    
    # Simula diferentes tipos de erro
    log_error("Busca Semântica", "Erro de conexão com API")
    time.sleep(0.1)
    
    try:
        # Simula uma exceção
        raise ValueError("Teste de exceção")
    except Exception as e:
        log_error("Sistema de Teste", "Erro simulado para teste", e)
    
def teste_logs_performance():
    """Testa logs de performance"""
    print("⚡ Testando logs de Performance...")
    
    # Simula medições de performance
    log_performance("Busca Semântica", 0.234)
    time.sleep(0.1)
    
    log_performance("Upload de Arquivo", 2.456, 150.5)
    time.sleep(0.1)
    
    log_performance("Geração de Relatório", 5.678)
    
def main():
    """Executa todos os testes de log"""
    print("="*60)
    print("🧪 TESTE COMPLETO DO SISTEMA DE LOGS")
    print("="*60)
    print()
    
    # Executa todos os testes
    teste_logs_busca_semantica()
    print()
    
    teste_logs_analise_dados()
    print()
    
    teste_logs_configuracoes()
    print()
    
    teste_logs_backend()
    print()
    
    teste_logs_api()
    print()
    
    teste_logs_sistema()
    print()
    
    teste_logs_erro()
    print()
    
    teste_logs_performance()
    print()
    
    print("="*60)
    print("✅ TESTE COMPLETO FINALIZADO!")
    print("📁 Verifique os arquivos de log na pasta 'logs/'")
    print("="*60)

if __name__ == "__main__":
    main()