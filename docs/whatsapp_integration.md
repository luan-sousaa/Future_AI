# Integração WhatsApp Business — Documentação Técnica

## Visão Geral

Este projeto conecta um agente de IA (Google ADK + Gemini) ao WhatsApp Business via **Meta Cloud API (oficial)**. Usuários enviam mensagens de texto pelo WhatsApp e recebem respostas do agente, que é capaz de buscar produtos no catálogo e processar pagamentos PIX.

---

## Arquitetura do Fluxo

```
┌──────────────┐
│ WhatsApp User│
└──────┬───────┘
       │ envia mensagem
       ▼
┌──────────────────┐
│  Meta Platform   │  (servidores da Meta)
└──────┬───────────┘
       │ POST /webhook  (JSON com payload da mensagem)
       ▼
┌─────────────────────────────────────────────┐
│  FastAPI Server  (src/services/main.py)     │
│  • GET  /webhook  → verificação Meta        │
│  • POST /webhook  → recebe mensagem         │
│  • POST /pagar    → endpoint de pagamento   │
└──────┬──────────────────────────────────────┘
       │ extrai phone + text via whatsapp_service.parse_incoming_message()
       ▼
┌─────────────────────────────────────────────┐
│  AgentRunner  (src/services/agent_runner.py)│
│  • Mantém sessão por número de telefone     │
│  • Invoca ADK Runner com a mensagem         │
└──────┬──────────────────────────────────────┘
       │ runner.run_async()
       ▼
┌─────────────────────────────────────────────┐
│  LlmAgent  (src/agent/retailer_agent.py)    │
│  • Modelo: Google Gemini                    │
│  • Tools: busca de produtos, pagamento PIX  │
└──────┬──────────────────────────────────────┘
       │ texto de resposta
       ▼
┌─────────────────────────────────────────────┐
│  WhatsAppService (src/services/             │
│                   whatsapp_service.py)      │
│  • send_message() → POST graph.facebook.com │
└──────┬──────────────────────────────────────┘
       │ entrega mensagem
       ▼
┌──────────────┐
│ WhatsApp User│
└──────────────┘
```

---

## Arquivos Relevantes

| Arquivo | Responsabilidade |
|---|---|
| `src/services/main.py` | Servidor FastAPI com os 3 endpoints |
| `src/services/whatsapp_service.py` | Parsing do payload Meta + envio de mensagens |
| `src/services/agent_runner.py` | Wrapper do ADK Runner, gerencia sessões por usuário |
| `src/agent/retailer_agent.py` | Definição do agente (modelo, prompt, tools) |
| `adk_app/agent.py` | Instancia `root_agent` para uso pelo Runner |
| `src/prompts/prompt.py` | System prompt do agente |
| `src/tools/` | Ferramentas: busca de produtos (Excel) e pagamento PIX |

---

## Setup Inicial

### 1. Meta Developer Console

1. Acesse [https://developers.facebook.com](https://developers.facebook.com) e faça login
2. Clique em **My Apps → Create App**
3. Escolha tipo: **Business**
4. Dê um nome ao app e clique em **Create App**
5. Na tela de produtos, encontre **WhatsApp** e clique em **Set up**

### 2. Obtendo as Credenciais

Na seção **WhatsApp → API Setup** do seu app:

- **`PHONE_NUMBER_ID`** — visível no campo "From" (ex: `123456789012345`)
- **`WHATSAPP_TOKEN`** — token temporário gerado automaticamente (dura 24h). Para produção, gere um **System User Token** permanente em Business Settings

### 3. Escolha o seu Verify Token

Defina uma string secreta de sua escolha (ex: `"meu-token-verificacao-abc123"`). Será usada para que a Meta confirme que o webhook é seu.

### 4. Instale o ngrok (para desenvolvimento local)

```bash
brew install ngrok
ngrok config add-authtoken <SEU_TOKEN_DO_NGROK>  # https://dashboard.ngrok.com
```

---

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha todos os campos:

```env
# Google / Gemini
GOOGLE_API_KEY=        # Chave da API do Google AI Studio (obrigatório)
MODEL=                 # Ex: gemini-2.0-flash (obrigatório)

# WhatsApp Business (Meta Cloud API)
WHATSAPP_TOKEN=        # Token de acesso da Meta (obrigatório)
PHONE_NUMBER_ID=       # ID do número de telefone no Meta Developer Console (obrigatório)
WEBHOOK_VERIFY_TOKEN=  # String secreta que você define para verificar o webhook (obrigatório)
```

| Variável | Onde encontrar | Obrigatório |
|---|---|---|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/) | Sim |
| `MODEL` | Documentação do Gemini (ex: `gemini-2.0-flash`) | Sim |
| `WHATSAPP_TOKEN` | Meta Developer Console → WhatsApp → API Setup | Sim |
| `PHONE_NUMBER_ID` | Meta Developer Console → WhatsApp → API Setup | Sim |
| `WEBHOOK_VERIFY_TOKEN` | Você define (qualquer string) | Sim |

---

## Como Rodar Localmente

### 1. Instale as dependências

```bash
pip install -r requirements.txt
```

### 2. Configure o `.env`

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

### 3. Suba o servidor FastAPI

```bash
uvicorn src.services.main:app --reload --port 8000
```

### 4. Exponha o servidor com ngrok (em outro terminal)

```bash
ngrok http 8000
# Anote a URL gerada: https://xxxx.ngrok.io
```

### 5. Configure o Webhook na Meta

No Meta Developer Console → **WhatsApp → Configuration → Webhook**:
- **Callback URL**: `https://xxxx.ngrok.io/webhook`
- **Verify Token**: o mesmo valor que você colocou em `WEBHOOK_VERIFY_TOKEN`
- Clique em **Verify and Save**
- Ative o subscription: **messages**

### 6. Adicione seu número como número de teste

Em **WhatsApp → API Setup**, adicione seu número pessoal clicando em **"Add phone number"**.

### 7. Envie uma mensagem

Envie uma mensagem de texto pelo WhatsApp para o número de teste fornecido pela Meta. O agente deve responder em segundos.

---

## Como Rodar em Produção

As diferenças em relação ao ambiente local:

1. **URL pública fixa**: substitua o ngrok por um servidor com IP/domínio fixo (VPS, AWS, GCP, Railway, etc.)
2. **HTTPS obrigatório**: a Meta exige HTTPS. Use Let's Encrypt ou o SSL do seu cloud provider.
3. **Token permanente**: gere um **System User Token** no Meta Business Settings (sem expiração de 24h)
4. **Número de produção**: registre um número real no Meta Business (não o número de teste)
5. **Variáveis de ambiente**: use secrets do seu provedor (não um arquivo `.env` em disco)

---

## Endpoints do Servidor

### `GET /webhook` — Verificação do Webhook

Chamado automaticamente pela Meta ao configurar o webhook. Valida o `WEBHOOK_VERIFY_TOKEN` e retorna o challenge.

**Query params:**
```
hub.mode=subscribe
hub.verify_token=<seu token>
hub.challenge=<string gerada pela Meta>
```

**Resposta (200):** retorna `hub.challenge` como texto puro.
**Resposta (403):** token inválido.

---

### `POST /webhook` — Recebe Mensagens do WhatsApp

Chamado pela Meta a cada mensagem recebida.

**Payload de entrada (exemplo):**
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "5511999999999",
          "type": "text",
          "text": { "body": "Quero comprar arroz" }
        }],
        "metadata": {
          "phone_number_id": "123456789"
        }
      }
    }]
  }]
}
```

**Comportamento:**
- Extrai `phone` e `text` da mensagem
- Ignora payloads sem mensagem de texto (retorna `{"status": "ignored"}`)
- Invoca o agente com contexto da sessão do usuário
- Envia resposta do agente de volta via WhatsApp
- Retorna `{"status": "ok"}`

---

### `POST /pagar` — Pagamento PIX (Mercado Pago)

**Body:**
```json
{
  "valor": 49.90,
  "email": "cliente@email.com",
  "first_name": "João",
  "last_name": "Silva"
}
```

**Resposta:** dados do pagamento PIX retornados pelo Mercado Pago.

---

## Sessões de Conversa

Cada número de telefone tem sua própria sessão de conversa. O histórico é mantido em memória (usando `InMemorySessionService` do ADK) enquanto o servidor estiver rodando.

- **`user_id`**: número de telefone do usuário (ex: `"5511999999999"`)
- **`session_id`**: gerado pelo ADK na primeira mensagem do usuário
- **Persistência**: apenas em memória — reiniciar o servidor apaga todas as sessões

Para persistência entre reinicializações, substitua `InMemorySessionService` por `DatabaseSessionService` (ADK suporta SQLite nativamente) em `src/services/agent_runner.py`.

---

## Limitações Conhecidas

1. **Apenas mensagens de texto**: áudios, imagens, documentos e stickers são ignorados silenciosamente
2. **QR Code PIX sem imagem**: o agente envia o código PIX como texto (copia-e-cola), não como imagem. Para enviar a imagem do QR Code, seria necessário fazer upload via Meta Media API antes de enviar
3. **Sessões em memória**: reiniciar o servidor encerra todas as conversas em andamento
4. **Token temporário**: o `WHATSAPP_TOKEN` padrão expira em 24h — em produção, use System User Token

---

## Como Adicionar Novas Ferramentas ao Agente

As ferramentas ficam em `src/tools/`. Para adicionar uma nova:

1. Crie uma função Python com parâmetros tipados e docstring descrevendo o que faz
2. O ADK usa a docstring como descrição da ferramenta para o modelo
3. Registre a ferramenta no agente em `src/agent/retailer_agent.py`, no array `tools=[]` passado ao `LlmAgent`
4. Se a ferramenta precisar de estado entre chamadas, use o parâmetro `tool_context: ToolContext` (ver exemplos em `db_tools_excel.py`)

---

## Troubleshooting Comum

### Webhook não verifica (403 Forbidden)
- Confirme que `WEBHOOK_VERIFY_TOKEN` no `.env` é exatamente igual ao configurado no Meta Developer Console
- Certifique-se de que o servidor está rodando e acessível pela URL do ngrok

### Mensagens não chegam / sem resposta
- Verifique se o subscription **"messages"** está ativo no webhook (Meta Developer Console → Webhook → Manage)
- Confirme que o ngrok ainda está rodando (ele expira se ficar inativo)
- Veja os logs do uvicorn para erros

### `WHATSAPP_TOKEN expired`
- Token temporário dura 24h — gere um novo em **WhatsApp → API Setup**
- Em produção, use System User Token permanente

### Agente não responde / erro no runner
- Verifique se `GOOGLE_API_KEY` e `MODEL` estão corretos no `.env`
- Confirme que o modelo definido em `MODEL` existe e está disponível

### `httpx.HTTPStatusError` ao enviar mensagem
- Token expirado ou `PHONE_NUMBER_ID` errado
- Verifique os valores no `.env`
