# Documentação de IA — Future AI Agent

## APIs e modelos utilizados

A aplicação é **provider-agnóstica**: o modelo é selecionado em tempo de execução pela variável `MODEL_PROVIDER`, através da factory `src/factories/model_factory.py`. Quatro backends são suportados:

| Provider | Modelo de referência | API / biblioteca | Uso |
|----------|---------------------|------------------|-----|
| **Ollama** (local) | `qwen2.5:7b-instruct` | API HTTP do Ollama | Padrão no Docker; inferência local, sem custo e sem nuvem |
| **Google Gemini** | `gemini-2.0-flash` | Google ADK / GenAI | Modelo em nuvem, suporta *thinking config* (planner) |
| **OpenAI** | `gpt-4.1-mini` | LiteLLM | Acesso à OpenAI via camada LiteLLM |
| **vLLM** (local) | `Qwen2.5-7B-Instruct` | API compatível com OpenAI | Servidor local de alto desempenho (GPU) |

A orquestração dos agentes é feita com o **Google ADK (Agent Development Kit)** — cada agente é um `LlmAgent` com tools registradas. Observabilidade via **Phoenix/OpenTelemetry** (OpenInference). *Não* são usados Anthropic nem LangChain.

## Contexto de uso

Dois agentes conversacionais em português operam o domínio de varejo/estoque:

- **Inventory Agent** — análise de inventário (estoque crítico, rupturas, itens inativos, diff por período).
- **Retailer Agent** — atendimento comercial (busca de produto, validação de estoque, pagamento simulado).

**Princípio central:** o LLM apenas *formula a resposta em linguagem natural*; todo dado factual (produto, preço, estoque, pagamento) vem exclusivamente de **tools** ligadas ao MongoDB. Os prompts proíbem explicitamente a invenção de dados — as tools são a única fonte de verdade.

## Prompts que sustentam o core

Os system prompts ficam em `src/prompts/`. Trechos que definem o comportamento essencial:

**Regra de não-alucinação (ambos os agentes):**
```
- Never invent product, price, stock, or payment data.
- Tools are the only source of truth.
- Do not say that information is unavailable if a previous tool result has it.
```

**Roteamento de tools (Inventory Agent):** o prompt mapeia intenção → tool, ex.:
```
- get_critical_stock_products: use for low stock, rupture, replenishment, critical inventory.
- get_inventory_diff_by_period: use for movement, variation, or inventory period analysis.
```

**Fluxo de venda controlado (Retailer Agent):**
```
- processar_pagamento: use only after explicit purchase confirmation, valid stock, and customer data.
- Never process payment without explicit confirmation.
```

## Exemplos de prompts que falharam

Durante o desenvolvimento (com foco em modelos locais de 7B, como o Qwen), vários comportamentos quebraram. Cada falha gerou uma regra defensiva no prompt atual:

| Falha observada | Prompt original (que falhou) | Correção aplicada |
|-----------------|------------------------------|-------------------|
| **Para após chamar a tool** — o modelo executava a tool e não gerava resposta ao usuário. | Prompt sem instrução de fechamento. | `After receiving tool results, ALWAYS generate a final natural language response. NEVER stop after a tool call.` |
| **Devolvia JSON cru** — expunha o retorno bruto da tool. | Sem regra de formatação. | `Never return raw JSON. Never expose raw field names from tools. Always rewrite them as natural Portuguese labels (Código, Produto, Preço, Estoque atual…).` |
| **Loop de tool** — chamava a mesma tool repetidamente para o mesmo pedido. | Sem guarda de repetição. | `NEVER repeatedly call the same tool for the same request unless: the previous call failed, the user requested updated data, or more parameters are required.` |
| **Re-perguntava dados já fornecidos** — pedia de novo nome/quantidade já ditos. | Prompt sem uso de contexto. | `Use conversation context. Do not ask again for data already given.` |
| **Inventava tipos de alerta** — criava categorias inexistentes (ex.: "estoque médio"). | Lista de alertas não fixada. | `Never invent alert types. Only use these alert types: critical, low_stock, zero_stock, rupture_risk, negative_stock, out_of_stock, inactive, overstocked, high_movement, low_movement.` |
| **Vazava raciocínio interno** — explicava o passo a passo do reasoning. | Sem restrição. | `Do not expose internal reasoning.` |

> **Lição de engenharia de prompt:** prompts longos e abstratos performam mal em modelos locais. A solução foi encurtar, usar regras imperativas (`NEVER` / `ALWAYS`) e mapear intenção→tool de forma explícita, em vez de descrever o comportamento desejado de modo genérico.
