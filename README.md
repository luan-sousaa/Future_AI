# Future AI Agent

Projeto com agentes baseados em Google ADK para apoiar operacoes de varejo e inventario.

Atualmente existem dois agentes principais:

- `inventory_agent`: analisa estoque, produtos criticos, rupturas, inativos e diferencas por periodo.
- `retailer_agent`: ajuda no fluxo comercial, busca produtos, valida estoque e processa pagamentos simulados.

## Estrutura

```text
inventory_app/          App ADK do agente de inventario
retailer_app/           App ADK do agente varejista
src/agent/              Definicao dos agentes
src/prompts/            Prompts dos agentes
src/tools/              Ferramentas chamadas pelos agentes
src/services/           Regras de negocio por dominio
src/factories/          Factory de modelo e planner
src/config/             Configuracoes de Mongo e alertas
src/observability/      Phoenix/OpenTelemetry
src/evals/              Estrutura de avaliacoes
src/datasets/           Datasets de inventario/fine-tuning
```

## Configuracao

Crie um ambiente virtual e instale as dependencias:

```bash
pip install -r requirements.txt
```

Para desenvolvimento/testes:

```bash
pip install -r requirements-dev.txt
```

Copie `.env.example` para `.env` e preencha as variaveis necessarias.

Exemplo para modelo local via Ollama:

```env
MODEL_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b-instruct
```

Exemplo para modelo local via vLLM:

```env
MODEL_PROVIDER=vllm
VLLM_MODEL=openai/Qwen/Qwen2.5-7B-Instruct
```

Exemplo para Gemini:

```env
MODEL_PROVIDER=gemini
GOOGLE_API_KEY=your_key
MODEL=gemini-2.0-flash
```

## MongoDB

Os agentes usam MongoDB como fonte de verdade para produtos, estoque, pagamentos e historico de vendas.

Variaveis principais:

```env
MONGO_READ_URI=
MONGO_WRITE_URI=
MONGO_DB_NAME=
MONGO_PRODUCTS_COLLECTION=
MONGO_PAYMENTS_COLLECTION=
MONGO_SALES_HISTORY_COLLECTION=
MONGO_INVENTORY_SNAPSHOTS_COLLECTION=
MONGO_INVENTORY_DIFF_COLLECTION=
```

## Rodando com ADK Web

Na raiz do projeto:

```bash
adk web
```

Depois escolha o app desejado na interface do ADK.

Tambem e possivel rodar apps separados:

```bash
adk web inventory_app
adk web retailer_app
```

## Observabilidade com Phoenix

Suba o Phoenix com Docker:

```bash
docker run --rm -p 6006:6006 -p 4317:4317 -i -t arizephoenix/phoenix:latest
```

Abra:

```text
http://localhost:6006
```

Variaveis recomendadas:

```env
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_PROJECT_NAME=future-ai-agent
```

Para separar traces por agente, rode cada app em um processo separado com project names diferentes:

```powershell
$env:PHOENIX_PROJECT_NAME="inventory_agent"
adk web inventory_app
```

```powershell
$env:PHOENIX_PROJECT_NAME="retailer_agent"
adk web retailer_app
```

## Fluxo das Tools

O agente varejista usa:

- `search_product_by_name`: busca produtos por nome.
- `get_product_by_code`: seleciona um produto exato.
- `get_product_stock_and_price_summary`: retorna estoque e preco dos produtos selecionados.
- `check_product_availability`: valida disponibilidade de estoque.
- `processar_pagamento`: gera pagamento mock, registra venda e baixa estoque.

O agente de inventario usa tools para visao geral, estoque critico, inativos e diferencas de inventario por periodo.

## Fine-tuning

Os scripts de fine-tuning ficam em:

```text
src/services/fine_tuning/
src/commands/
```

Dependencias pesadas de treino local ficam separadas em:

```text
src/services/fine_tuning/requirements-finetune.txt
```

## Testes

Quando as dependencias de desenvolvimento estiverem instaladas:

```bash
pytest
```

## Observacoes

- Nao instale `bson` separadamente; ele ja vem com `pymongo`.
- Os prompts foram mantidos curtos para funcionar melhor com modelos locais como Qwen.
- As tools devem ser a fonte de verdade para dados de produto, estoque e pagamento.
