# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Future AI Agent** is a Portuguese-language retail and inventory management system built on Google ADK (Agent Development Kit). It exposes two LLM agents:

- **Inventory Agent** — analyzes stock levels, ruptures (stockouts), inactive items, and inventory trends
- **Retailer Agent** — product discovery, stock validation, and simulated payment processing

## Commands

### Setup
```bash
pip install -r requirements.txt        # Core dependencies
pip install -r requirements-dev.txt    # Dev + testing
cp .env.example .env                   # Configure environment
```

### Running Agents (local)
```bash
adk web                                # Launch ADK web UI (both agents)
adk web inventory_app                  # Inventory agent only
adk web retailer_app                   # Retailer agent only
adk api_server . --host 0.0.0.0 --port 8000   # REST API consumed by Streamlit
streamlit run streamlit_app.py         # Dashboard + agent chat (needs api_server)
```

### Running with Docker (self-contained)
```bash
cp .env.example .env                   # Set GOOGLE_API_KEY/OPENAI_API_KEY; Mongo defaults work as-is
docker compose up --build              # mongo, mongo-seed, agent-api, streamlit, phoenix
```
- Streamlit: http://localhost:8501 · ADK API: http://localhost:8000 · Phoenix: http://localhost:6006
- The stack is **self-contained**: a bundled `mongo` service is seeded on startup
  by `mongo-seed`, which runs `python -m src.repositories.data_to_mongo` to load
  the products collection from `src/repositories/historico_vendas_semanal_36m (2).xlsx`.
  No external database is required — only a model API key.
- `mongo-seed` runs `delete_many({})` then re-imports, so it **re-seeds on every
  `up`**. The `products` data is rebuilt; `payments`/`sales_history` are written at
  runtime; `inventory_snapshots`/`inventory_diff` stay empty (period-diff tool needs
  separately generated snapshots).
- `agent-api` and `streamlit` share one image (built once); the API serves both
  `inventory_app` and `retailer_app`. Compose overrides `MONGO_READ_URI`/
  `MONGO_WRITE_URI` to the `mongo` service, `AGENT_API_URL` to `http://agent-api:8000`,
  and `PHOENIX_ENDPOINT` to `http://phoenix:6006/v1/traces`.
- **To use external MongoDB (Atlas) instead:** delete the `mongo`/`mongo-seed`
  services and the `*mongo-uris` overrides, and set the URIs in `.env`.
- **After editing Python code, rebuild the image:** `docker compose up -d --build`
  (or `docker compose build`). A plain `docker compose up -d` reuses the existing
  `future-ai-agent:latest` image, so `src/` changes won't reach the container until
  a rebuild — a stale image was the root cause of a `localhost:11434` connection
  error even with `OLLAMA_API_BASE` correctly overridden.
- **Model provider:** the stack runs Ollama by default. A bundled `ollama` service
  serves the model; `ollama-pull` downloads `OLLAMA_MODEL` (~GBs) on first `up` into
  the `ollama-data` volume. Compose overrides `OLLAMA_API_BASE` to `http://ollama:11434`.
  On a GPU host (VM), uncomment the `deploy.resources` block on the `ollama` service
  (needs nvidia-container-toolkit); on CPU, inference is slow.
  - For local dev against a host Ollama (e.g. with GPU on your workstation), point the
    container at it with `OLLAMA_API_BASE=http://host.docker.internal:11434` and remove
    the `ollama`/`ollama-pull` services.
  - To use a cloud model instead, set `MODEL_PROVIDER=gemini` (or `openai`) and the
    corresponding API key in `.env`.

### Testing
```bash
pytest                                 # All tests (configured to src/tests/)
pytest src/tests/test_foo.py           # Single test file
pytest -k "test_name"                  # Single test by name
```

### Linting
```bash
flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src --count --exit-zero --max-complexity=10 --max-line-length=127
pylint src/tools/ src/repositories/product_model.py src/tests/ --fail-under=7.0
```

### Observability (Phoenix tracing)
```bash
docker run --rm -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest
```

## Architecture

### Entry Points
| File | Purpose |
|------|---------|
| `inventory_app/runner.py` | ADK runner for the inventory agent |
| `retailer_app/runner.py` | ADK runner for the retailer agent |
| `streamlit_app.py` | Dashboard UI for product monitoring |
| `src/services/whatsapp/whatsapp_service.py` | WhatsApp Business webhook |

### Agent Construction Flow
1. `*_app/agent.py` instantiates an `LlmAgent` from Google ADK
2. Model is resolved via `src/factories/model_factory.py` — supports **Gemini**, **OpenAI** (LiteLLM), **Ollama**, and **vLLM**; provider is selected by an environment variable
3. Planner (thinking config) is resolved via `src/factories/planner_factory.py` — only supported on Google Gemini
4. Tools from `src/tools/` are registered on the agent as decorated callables
5. Observability is bootstrapped via `src/observability/phoenix.py` at startup, with per-agent Phoenix project isolation

### Key Source Directories
| Directory | Purpose |
|-----------|---------|
| `src/agent/` | Agent definitions (`inventory_agent.py`, `retailer_agent.py`) |
| `src/prompts/` | System prompts (Portuguese, low-temperature, data-grounded) |
| `src/tools/` | Agent-callable tools: `mongo_tools.py`, `payment_tools.py`, `db_tools_excel.py` |
| `src/services/` | Business logic: inventory, payment, sales, mongo, email, whatsapp, fine_tuning |
| `src/repositories/` | Model provider clients + `product_model.py` |
| `src/factories/` | `model_factory.py`, `planner_factory.py` |
| `src/observability/` | Phoenix/OTEL setup, per-agent callbacks |
| `src/evals/` | Evaluation engine, runners, metrics, datasets, schemas, traces |
| `src/config/` | MongoDB config, alert system, ADK eval web config |

### Tool Pattern
All agent tools follow this signature convention:
```python
def tool_name(tool_context: ToolContext, ...) -> dict | list:
    ...
```
Tools are the canonical interface between the LLM and MongoDB — the prompts explicitly instruct agents never to invent data.

### MongoDB
- Separate **read** and **write** URIs (`MONGO_READ_URI` / `MONGO_WRITE_URI`) for read scaling
- Collections: `products`, `payments`, `sales_history`, `inventory_snapshots`, `inventory_diff`
- All DB access goes through `MongoService` in `src/services/mongo/`

### Observability
Phoenix distributed tracing (OTEL-based) is initialized on agent startup. Each agent runs in its own Phoenix project. Tool-level tracing is instrumented via OpenInference callbacks in `src/observability/`.

### Evaluation Framework
- EVALSET files live in `*_app/*.evalset.json` and `src/evals/datasets/`
- Custom metrics are in `src/evals/metrics/`
- Traces can be replayed and analyzed from `src/evals/traces/`

## Environment Variables

See `.env.example` for the full list. Key variables:
- `MODEL_PROVIDER` — selects `gemini` | `openai` | `ollama` | `vllm`
- `MONGO_READ_URI` / `MONGO_WRITE_URI`
- `PHOENIX_ENDPOINT` — OTEL collector URL (default: `http://localhost:4317`)
- Google Cloud / Gemini API credentials

## Language Note

All prompts, agent instructions, error messages, and most documentation are in **Brazilian Portuguese**. Keep this consistent when editing prompts or user-facing strings.
