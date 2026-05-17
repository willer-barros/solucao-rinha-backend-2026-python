# Rinha de Backend 2026 — Solução Python (Detecção de Fraude)

Este repositório contém a minha solução para a Rinha de Backend, focada em alta performance, concorrência extrema e baixa latência utilizando o ecossistema Python. 

A aplicação foi projetada para receber payloads de transações financeiras, realizar a normalização de variáveis em tempo real e executar uma busca espacial por vizinhos mais próximos (KNN) para determinar o score de fraude de cada operação.

## 🚀 Resultados do Teste de Carga (k6)

Sob o cenário estrito de restrição de hardware da competição, o motor superou a marca de **25 mil requisições processadas** em um curto intervalo de stress, mantendo estabilidade absoluta.

* **Taxa de Sucesso:** 100.00% (0.00% de falhas)
* **Vazão Média:** ~900 Requisições por Segundo (RPS)
* **Mediana de Latência (`med`):** 16.63ms
* **Volume Total Controlado:** 27.030 requisições sem nenhum drop de conexão.

---

## 🛠️ Stack Tecnológica & Arquitetura

A arquitetura replica exatamente o ambiente oficial da Rinha, distribuindo a carga através de um balanceador e limitando os recursos computacionais via Docker:

* **FastAPI:** Framework web assíncrono de alto rendimento. A rota principal foi desenhada de forma puramente assíncrona para eliminar o overhead de troca de contexto de threads (*context switching*) sob alta concorrência.
* **Uvicorn (Multi-Workers):** Gerenciador de processos ASGI configurado com múltiplos workers por container para contornar o GIL (*Global Interpreter Lock*) do Python, maximizando o uso das fatias de CPU disponíveis.
* **USearch:** Motor de busca vetorial altamente otimizado em C++ executado nativamente em memória. Substitui abordagens tradicionais de banco de dados para garantir buscas KNN de 14 dimensões em frações de milissegundos.
* **NumPy:** Utilizado para inferência matricial ultrarrápida das labels binárias mapeadas em memória.
* **Nginx:** Atuando como Load Balancer na porta `9999`, distribuindo o tráfego via algoritmo *round-robin* com otimizações de *proxy buffering* desabilitado para vazão imediata de dados.

---

## 📐 Topologia da Infraestrutura (Restrições de Hardware)

Os limites foram configurados estritamente no `docker-compose.yml` para simular o ambiente de produção da rinha:

* **`load_balancer` (Nginx):** 0.10 CPU, 20MB RAM
* **`api_instance_1` (FastAPI):** 0.45 CPU, 165MB RAM
* **`api_instance_2` (FastAPI):** 0.45 CPU, 165MB RAM

---

## 🏃‍♂️ Como Executar o Projeto Localmente

### Pré-requisitos
* Docker e Docker Compose instalados.
* O arquivo `data/references.json.gz` posicionado corretamente na pasta de dados.

### 1. Compilar a imagem base (Quebrando o cache local)
Para garantir que o script `build_index.py` processe o arquivo de referências atualizado e monte os binários do índice do USearch de forma limpa, execute:
```bash
docker compose build --build-arg CACHE_BUST=$(date +%s)

### Subir serviços em background
1 - docker compose up -d

### Verificar os indices
1 - docker compose logs -f

### Como Rodar o teste de stress k6
docker run --rm -i --add-host=host.docker.internal:host-gateway grafana/k6 run - <script.js
