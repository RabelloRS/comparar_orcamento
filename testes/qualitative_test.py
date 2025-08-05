# /testes/qualitative_test.py
import requests
import json
import os

# --- Configuração ---
API_URL = "http://localhost:8000/buscar"
TEST_SUITE_PATH = "testes/test_suite_v3.json"

def run_qualitative_test():
    """
    Executa as queries da suíte de testes e exibe os 3 melhores resultados
    para cada uma, permitindo uma análise qualitativa.
    """
    print("="*80)
    print("INICIANDO SESSÃO DE TESTE QUALITATIVO COM A NOVA BASE DE CONHECIMENTO")
    print("="*80)

    try:
        with open(TEST_SUITE_PATH, 'r', encoding='utf-8') as f:
            # Suporta a estrutura de dicionário com a chave 'test_cases'
            test_data = json.load(f)
            test_cases = test_data.get('test_cases', [])
    except FileNotFoundError:
        print(f"ERRO: Arquivo de testes '{TEST_SUITE_PATH}' não encontrado.")
        return
    except json.JSONDecodeError:
        print(f"ERRO: O arquivo '{TEST_SUITE_PATH}' não é um JSON válido.")
        return

    if not test_cases:
        print("AVISO: Nenhum caso de teste encontrado no arquivo.")
        return

    for i, test in enumerate(test_cases, 1):
        query = test.get('query')
        if not query:
            continue

        print(f"\n--- [{i}/{len(test_cases)}] TESTANDO QUERY: \"{query}\" ---")
        
        payload = {"texto_busca": query, "top_k": 3}
        
        try:
            response = requests.post(API_URL, json=payload, timeout=120)
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                if not results:
                    print("  -> Nenhum resultado retornado pela API.")
                else:
                    for item in results:
                        # Limpa a descrição para melhor legibilidade, mostrando apenas a parte original
                        clean_desc = item['descricao'].split('|')[0].strip() if item['descricao'] != 'N/A' else 'Descrição não disponível'
                        score = item.get('semantic_score', item.get('score', 0.0))
                        print(f"  {item['rank']}. [CÓDIGO: {item['codigo']}] [Score: {score:.4f}]")
                        print(f"     Descrição: {clean_desc}")
                        print(f"     Preço: R$ {item.get('preco', 0.0):.2f} | Unidade: {item.get('unidade', 'N/A')} | Fonte: {item.get('fonte', 'N/A')}")
                        print()
            else:
                print(f"  -> ERRO na API: Status {response.status_code} - {response.text}")

        except requests.RequestException as e:
            print(f"  -> ERRO de conexão com a API: {e}")

    print("\n" + "="*80)
    print("SESSÃO DE TESTE QUALITATIVO CONCLUÍDA")
    print("="*80)

if __name__ == "__main__":
    run_qualitative_test()