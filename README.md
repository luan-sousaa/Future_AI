# Future AI Agent

Sistema de varejo e gestão de inventário construído sobre o **Google ADK (Agent Development Kit)**. Expõe dois agentes LLM em português que operam sob uma restrição central: o modelo decide *como responder*, mas todo dado factual vem de **tools** acopladas ao MongoDB — os prompts instruem os agentes a nunca sintetizar produto, estoque ou preço.

O projeto é **provider-agnóstico** (Gemini, OpenAI/LiteLLM, Ollama, vLLM) e **deploy-agnóstico** (local via ADK ou stack completo via Docker Compose). A troca é feita por variável de ambiente, sem alteração de código.

## Os dois agentes

- **Inventory Agent** — análise de estoque: produtos críticos, rupturas (stockouts), itens inativos e diff de inventário entre períodos.
- **Retailer Agent** — fluxo comercial: descoberta de produtos, validação de disponibilidade e processamento de pagamento simulado (que dá baixa no estoque e registra a venda).

## Arquitetura

O ciclo de uma requisição:

1. **Entrada** — interface web do ADK, dashboard Streamlit ou a REST API (`adk api_server`).
2. **Construção do agente** — `*_app/agent.py` instancia um `LlmAgent`. O modelo é resolvido em `src/factories/model_factory.py` a partir de `MODEL_PROVIDER`; o planner (thinking config, só Gemini) em `src/factories/planner_factory.py`.
3. **Execução** — as tools de `src/tools/` (`mongo_tools`, `payment_tools`, `db_tools_excel`) são a interface canônica entre o LLM e o MongoDB. Toda leitura/escrita passa por `MongoService` (`src/services/mongo/`), com URIs de **read** e **write** separadas.
4. **Observabilidade** — tracing distribuído via Phoenix/OpenTelemetry, inicializado no startup (`src/observability/phoenix.py`), com projeto Phoenix isolado por agente e instrumentação OpenInference nas tools.

## Execução via Docker (stack autossuficiente)

Sobe o ambiente completo — `mongo`, `mongo-seed`, `agent-api`, `streamlit`, `phoenix` e (por padrão) `ollama` — sem dependências externas além de uma chave de modelo.

```bash
cp .env.example .env          # defina GOOGLE_API_KEY/OPENAI_API_KEY; as URIs do Mongo já apontam pro serviço bundled
docker compose up --build
```

| Serviço | Endpoint |
|---------|----------|
| Streamlit (dashboard) | http://localhost:8501 |
| ADK REST API | http://localhost:8000 |
| Phoenix (traces) | http://localhost:6006 |

Notas operacionais:

- **Seeding:** `mongo-seed` roda `python -m src.repositories.data_to_mongo`, fazendo `delete_many({})` + reimport a cada `up` — a collection `products` é reconstruída; `payments`/`sales_history` são populadas em runtime.
- **Overrides:** o Compose injeta `MONGO_READ_URI`/`MONGO_WRITE_URI` → serviço `mongo`, `AGENT_API_URL` → `http://agent-api:8000`, `PHOENIX_ENDPOINT` → `http://phoenix:6006/v1/traces` e `OLLAMA_API_BASE` → `http://ollama:11434`.
- **Modelo:** `ollama-pull` baixa `OLLAMA_MODEL` (alguns GB) no volume `ollama-data` na primeira subida. Em host com GPU, descomente `deploy.resources` no serviço `ollama` (requer nvidia-container-toolkit); em CPU a inferência é lenta.
- **MongoDB externo (Atlas):** remova os serviços `mongo`/`mongo-seed` e os overrides `*mongo-uris`, e defina as URIs no `.env`.
- **Após mudar código Python, rebuilde a imagem:** `docker compose up -d --build` (ou `docker compose build`). Um `docker compose up -d` sozinho reaproveita a imagem antiga, então alterações em `src/` não entram no container até o rebuild.

## Execução local (desenvolvimento)

```bash
pip install -r requirements.txt          # core
pip install -r requirements-dev.txt      # testes + lint
cp .env.example .env

adk web                                  # UI do ADK com os dois agentes, para teste
adk api_server . --host 0.0.0.0 --port 8000   # REST API consumida pelo Streamlit
streamlit run streamlit_app.py           # dashboard (requer a api_server no ar)
```

Apps isolados: `adk web inventory_app` · `adk web retailer_app`.

## Configuração de modelo

`MODEL_PROVIDER` seleciona o cliente em `model_factory`:

```env
# Ollama — inferência local, padrão do Docker
MODEL_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_API_BASE=http://localhost:11434       # host Ollama a partir de container: http://host.docker.internal:11434

# Gemini
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=...
MODEL=gemini-2.0-flash

# OpenAI via LiteLLM
MODEL_PROVIDER=openai
OPENAI_API_KEY=...
LITELLM_MODEL=openai/gpt-4.1-mini-2025-04-14

# vLLM (reutiliza OPENAI_API_KEY)
MODEL_PROVIDER=vllm
VLLM_MODEL=openai/Qwen/Qwen2.5-7B-Instruct
VLLM_API_BASE=http://localhost:8000/v1
```

## Estrutura

```text
inventory_app/      App ADK + runner do agente de inventário
retailer_app/       App ADK + runner do agente varejista
streamlit_app.py    Dashboard de monitoramento + chat
src/agent/          Definição dos LlmAgent
src/prompts/        System prompts (PT, baixa temperatura, ancorados em dados)
src/tools/          Tools agent-callable — única ponte LLM ↔ Mongo
src/services/       Lógica de negócio (inventory, payment, sales, mongo, email, whatsapp, fine_tuning)
src/factories/      model_factory, planner_factory
src/repositories/   Clientes de provider de modelo + product_model
src/observability/  Setup Phoenix/OTEL + callbacks por agente
src/evals/          Engine de avaliação, runners, métricas, schemas, traces
src/config/         Config do Mongo, sistema de alertas
```

## Testes e lint

```bash
pytest                          # suíte completa (configurada em src/tests/)
pytest -k "nome_do_teste"       # teste isolado

flake8 src --select=E9,F63,F7,F82 --show-source     # erros de sintaxe/nome
pylint src/tools/ src/repositories/product_model.py src/tests/ --fail-under=7.0
```

## Convenções

- **Tools são a fonte de verdade** para produto, estoque e pagamento — dado fora desse canal não entra na resposta.
- Prompts mantidos curtos para melhor aderência de modelos locais (Qwen).
- `bson` **não** deve ser instalado à parte — já acompanha `pymongo`.
- Strings de prompt, instruções e mensagens ao usuário são em **português brasileiro**; mantenha a consistência ao editar.
