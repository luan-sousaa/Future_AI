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

**Roteamento de tools (Inventory Agent):** o prompt mapeia intenção → **tool nomeada
sem parâmetros** (zero-arg), ex.:
```
- list_low_stock_products: estoque abaixo do mínimo / reposição.
- list_out_of_stock_products: produtos sem estoque / em ruptura.
- list_overstocked_products / list_inactive_products: excesso / inativos.
- list_top_selling_products / list_slow_moving_products: giro alto / baixo.
- get_inventory_diff_by_period: movimentação ou variação por período.
- search_product_by_name → get_product_commercial_context: detalhe de um produto
  citado por nome (o código é resolvido internamente, via estado da sessão).
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
| **Inventava tipos de alerta** — criava categorias inexistentes (ex.: "estoque médio"). | Tipo de alerta era um parâmetro livre passado pelo modelo. | **Correção estrutural:** as condições viraram **tools nomeadas dedicadas** (`list_low_stock_products`, `list_out_of_stock_products`, `list_overstocked_products`, `list_inactive_products`, `list_top_selling_products`, `list_slow_moving_products`). Sem campo de tipo de alerta, o modelo não tem como inventar categoria. |
| **Vazava raciocínio interno** — explicava o passo a passo do reasoning. | Sem restrição. | `Do not expose internal reasoning.` |
| **Argumentos malformados em modelos pequenos** — o 3B passava o schema (`{"type":"integer"}`) no lugar do valor de `limit`/`skip`, quebrando a busca. | Parâmetros operacionais expostos ao LLM. | **Correção estrutural:** parâmetros como `limit`/`skip` saíram da assinatura visível ao LLM (fixados internamente). Tools de lista ficaram zero-arg. |
| **Inventava código de produto** — ao pedir estoque de um produto citado por nome, o modelo fabricava um código (ex.: `TABACO_LAREVOLUCION`). | Tool exigia `product_code` e o prompt não orientava buscar primeiro. | Regra de prompt: *"sempre `search_product_by_name` primeiro; nunca inventar código"*. **+ Correção estrutural:** `get_product_by_code` saiu do inventário e o `get_product_commercial_context` resolve o código pelo estado da sessão. |
| **Busca por frase exata não achava** — "cerveja amstel" retornava vazio (dado abreviado "CERV AMSTEL"). | Termo casado como substring contígua. | **Correção estrutural:** busca **tokenizada** (cada palavra casa em qualquer ordem) com fallback para qualquer-palavra, ignorando tokens curtos. |

> **Lição de engenharia de prompt:** prompts longos e abstratos performam mal em
> modelos locais. A solução foi encurtar, usar regras imperativas (`NEVER` / `ALWAYS`)
> e mapear intenção→tool de forma explícita.
>
> **Lição de design de tools (igualmente importante):** muitos erros de modelos
> menores não se resolvem no prompt, e sim **reduzindo a superfície de argumentos**.
> Todo parâmetro exposto ao LLM é algo que ele pode malformar — por isso preferimos
> **tools nomeadas zero-arg** e resolução de identificadores (código de produto) pelo
> **estado da sessão**, em vez de pedir que o modelo os forneça.
