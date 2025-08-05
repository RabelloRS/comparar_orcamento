#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para capturar erro específico
"""

import requests
import json

def test_failing_query():
    """
    Testa a query que sabemos que falha para capturar o traceback
    """
    url = "http://localhost:8000/buscar"
    
    # Query que sabemos que causa erro
    query_data = {
        "texto_busca": "bloco de concreto estrutural 14x19x39cm",
        "top_k": 3
    }
    
    print(f"🔍 Testando query que falha: '{query_data['texto_busca']}'")
    print("📡 Enviando requisição para a API...")
    
    try:
        response = requests.post(url, json=query_data, timeout=30)
        
        if response.status_code == 200:
            print("✅ Sucesso inesperado! A query funcionou.")
            data = response.json()
            print(f"📊 Resultados: {len(data.get('results', []))} encontrados")
        else:
            print(f"❌ ERRO CAPTURADO! Status: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            print("\n🔍 AGORA VERIFIQUE O TERMINAL DO SERVIDOR PARA O TRACEBACK COMPLETO!")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        print("🔍 Verifique se o servidor está rodando em http://localhost:8000")

if __name__ == "__main__":
    test_failing_query()