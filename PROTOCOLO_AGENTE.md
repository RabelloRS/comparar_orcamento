# 📋 PROTOCOLO DE OPERAÇÕES PARA O AGENTE DE IA

Este é o conjunto de instruções fixas e regras que devem ser seguidas em **todas** as interações dentro deste projeto. O objetivo é garantir a estabilidade, consistência e sucesso do desenvolvimento.

---

### **1. Princípios Fundamentais (Sempre Verifique Primeiro)**

1.  **Pasta Raiz:** A sua pasta de trabalho atual é a **raiz do projeto**. Todos os caminhos de arquivos e comandos devem ser executados a partir daqui, a menos que uma instrução especifique o contrário (ex: `cd testes`).
2.  **Ambiente Virtual (`.venv`):** **NENHUM** comando Python (`python`, `pip`, `uvicorn`, `streamlit`) pode ser executado antes de garantir que o ambiente virtual está ativado. Sempre verifique o prompt do terminal.
    * **Comando para Ativar:** `.\.venv\Scripts\activate` (no Windows) ou `source .venv/bin/activate` (no Linux/Mac).
3.  **Código Completo no CANVAS:** Conforme a diretriz principal, sempre que um arquivo for modificado, o código completo e atualizado deve ser colocado no CANVAS. Evite suprimir trechos com "...". A reescrita completa é preferível para garantir que não haja erros de contexto.

---

### **2. Gerenciamento de Dependências (Regras do `pip`)**

1.  **Antes de Instalar:** Antes de adicionar uma nova biblioteca, primeiro salve o estado atual das dependências.
    * **Comando:** `pip freeze > requirements_antes.txt`
2.  **Instalação:** Instale a nova biblioteca.
    * **Comando:** `pip install nome_da_biblioteca`
3.  **Após Instalar:** Após a instalação bem-sucedida, atualize o arquivo `requirements.txt` oficial.
    * **Comando:** `pip freeze > requirements.txt`

---

### **3. Fluxo de Execução e Modificação**

1.  **Processamento de Dados:** Se a tarefa envolve modificar como os dados são lidos, enriquecidos ou processados (qualquer alteração nos arquivos da pasta `/data_extraction/` ou no `knowledge_pipeline.py`), siga este fluxo:
    * **Passo 1:** Faça a alteração no código.
    * **Passo 2:** **Apague** a pasta `/dados/cache` e o arquivo `dados/knowledge_base.csv` para forçar uma reconstrução completa.
    * **Passo 3:** Execute o script de construção da base de conhecimento (ex: `python knowledge_pipeline.py`).
    * **Passo 4:** Apenas depois, reinicie o servidor da API.

2.  **Lógica da IA:** Se a tarefa envolve modificar a lógica de um agente (qualquer arquivo na pasta `/app/`), siga este fluxo:
    * **Passo 1:** Faça a alteração no código.
    * **Passo 2:** Reinicie o servidor da API para que as novas alterações sejam carregadas.
    * **Comando:** `uvicorn app.main:app --reload`

3.  **Interface Gráfica:** Se a tarefa envolve modificar a interface (`interface.py`), siga este fluxo:
    * **Passo 1:** Faça a alteração no código.
    * **Passo 2:** O Streamlit irá detetar a alteração e oferecer a opção de "Rerun" na própria interface web. Se não, basta reiniciar o processo no terminal.
    * **Comando:** `streamlit run interface.py`

---

### **4. Protocolo de Validação**

1.  **Após Qualquer Mudança Crítica:** Depois de qualquer alteração na lógica da IA (`/app/`) ou no processamento de dados, a validação automatizada **deve** ser executada.
2.  **Suíte de Testes Padrão:** Use sempre a suíte de testes mais recente e validada. Atualmente, é a `test_suite_v3.json`.
3.  **Comando de Validação:**
    ```bash
    # Navegue para a pasta de testes e execute
    cd testes
    python validator.py test_suite_v3.json
    cd .. 
    ```
4.  **Análise de Resultados:** Sempre compare a nova precisão (Top-1 e Top-3) com a da execução anterior para medir o impacto da mudança.

---

### **Checklist Rápido Antes de Agir:**

- [ ] O ambiente virtual está ativado?
- [ ] Estou na pasta raiz do projeto?
- [ ] A tarefa envolve dados, IA ou interface? Qual fluxo devo seguir?
- [ ] Após a mudança, preciso rodar a validação?

Seguir este protocolo rigorosamente irá minimizar erros, evitar a corrupção de dados e garantir que cada passo do desenvolvimento seja um avanço sólido em direção ao nosso objetivo.