import json
import requests
import pandas as pd
import sys
from datetime import datetime
from requests.exceptions import RequestException

API_URL = "http://localhost:8000/buscar"
TEST_SUITE_PATH = "test_suite.json"

def run_validation(test_file=None):
    """
    Executa a suíte de testes contra a API e calcula as métricas de precisão.
    """
    # Verificar se foi fornecido o arquivo de teste como argumento
    if test_file is None:
        if len(sys.argv) > 1:
            test_file = sys.argv[1]
        else:
            test_file = TEST_SUITE_PATH
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
            # Suporta ambas as estruturas: lista direta ou dicionário com 'test_cases'
            if isinstance(test_data, list):
                test_cases = test_data
            else:
                test_cases = test_data.get('test_cases', test_data)
    except FileNotFoundError:
        print(f"ERRO: Arquivo de testes '{test_file}' não encontrado.")
        return
    
    total_tests = len(test_cases)
    top_1_hits = 0
    top_3_hits = 0
    results_log = []

    print(f"Iniciando validação com {total_tests} casos de teste...")

    for i, test in enumerate(test_cases, 1):
        query = test['query']
        expected_codes = test['expected_codes']
        
        try:
            # Fazer requisição para a API
            payload = {'texto_busca': query, 'top_k': 3}
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            
            # Extrair os códigos dos resultados
            results = response.json()['results']
            predicted_codes = [item['codigo'] for item in results[:3]]
            
            # Calcular métricas
            top_1_hit = predicted_codes[0] in expected_codes if predicted_codes else False
            top_3_hit = any(code in expected_codes for code in predicted_codes)
            
            if top_1_hit:
                top_1_hits += 1
            if top_3_hit:
                top_3_hits += 1
            
            print(f"Teste {i}: Query='{query}', Esperado={expected_codes}, Top 3={predicted_codes}")
            
            results_log.append({
                'id': i,
                'query': query,
                'expected_codes': expected_codes,
                'predicted_codes': predicted_codes,
                'top_1_hit': top_1_hit,
                'top_3_hit': top_3_hit
            })
            
        except RequestException as e:
            print(f"ERRO ao chamar a API para o teste {i}: {e}")
            results_log.append({
                'id': i,
                'query': query,
                'expected_codes': expected_codes,
                'predicted_codes': [],
                'top_1_hit': False,
                'top_3_hit': False,
                'error': str(e)
            })

    print("\n--- Validação Concluída ---")
    
    # Calcular métricas finais
    precision_top_1 = (top_1_hits / total_tests) * 100 if total_tests > 0 else 0
    precision_top_3 = (top_3_hits / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\nRESULTADOS:")
    print(f"Total de testes: {total_tests}")
    print(f"Acertos Top-1: {top_1_hits} ({precision_top_1:.2f}%)")
    print(f"Acertos Top-3: {top_3_hits} ({precision_top_3:.2f}%)")
    
    # Salvar log detalhado
    df = pd.DataFrame(results_log)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"validation_log_{timestamp}.csv"
    df.to_csv(log_filename, index=False, encoding='utf-8')
    print(f"\nLog detalhado salvo em: {log_filename}")
    
    return {
        'total_tests': total_tests,
        'top_1_hits': top_1_hits,
        'top_3_hits': top_3_hits,
        'precision_top_1': precision_top_1,
        'precision_top_3': precision_top_3,
        'results_log': results_log
    }

if __name__ == "__main__":
    run_validation()