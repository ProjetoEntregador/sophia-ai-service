# Sophia AI Service

Microserviço de IA do projeto **Sophia / Pechinchou**. Expõe uma API HTTP
(Flask) que concentra as capacidades de inteligência artificial consumidas pelo
bot: **chat com tool calling**, **transcrição de áudio (STT)** e **leitura de
receitas médicas via OCR**.

O chat usa uma **cadeia de provedores com fallback automático**: se o provedor
primário falhar (ex.: rate limit), a requisição cai para o próximo provedor sem
quebrar a conversa.

---

## Funcionalidades

| Recurso | Descrição | Modelo padrão |
|---|---|---|
| **Chat** | Conversa com suporte a *tool calling*, com fallback entre provedores | `gemini-2.5-flash` → `llama-3.3-70b-versatile` (Groq) |
| **STT** | Transcrição de áudio para texto (português) | `whisper-large-v3` (Groq) |
| **OCR** | Extração estruturada de medicamentos de receitas (visão) | `llama-4-scout-17b` (Groq) |

---

## Stack

- **Linguagem:** Python 3.12
- **Framework web:** Flask
- **Provedores de IA:**
  - [Groq](https://groq.com) (SDK `groq`) — chat, STT (Whisper) e OCR (visão)
  - [Google Gemini](https://ai.google.dev) — fallback de chat, via endpoint compatível com OpenAI (SDK `openai`)
- **Infra:** Docker + Docker Compose

---

## Arquitetura

A camada de IA é separada dos serviços de aplicação e aplica alguns padrões de
projeto para manter o código extensível e sem repetição:

```
src/
├── ai/                      # Infraestrutura de IA
│   ├── base.py              # ChatProvider (ABC)        → Strategy (contrato)
│   ├── openai_compat.py     # OpenAICompatProvider      → Adapter (Groq/Gemini)
│   └── factory.py           # AIClientFactory           → Factory (clientes + cadeia)
├── services/                # Regras de negócio
│   ├── chat.py              # ChatService               → Chain of Responsibility (fallback)
│   ├── stt.py               # SpeechToText
│   └── ocr.py               # OCRService
├── controllers/             # Rotas Flask (blueprints)
│   ├── ai.py                # /ai/health
│   ├── chat.py              # /chat/completions
│   ├── stt.py               # /stt/transcribe
│   └── ocr.py               # /ocr/read
├── factory/
│   └── create_app.py        # Application factory + injeção de dependências
└── prompts.py               # Prompts do OCR
```

| Padrão | Onde | Papel |
|---|---|---|
| **Strategy** | `ChatProvider` | Contrato comum; provedores intercambiáveis |
| **Adapter** | `OpenAICompatProvider` | Adapta clientes Groq/Gemini ao contrato |
| **Factory** | `AIClientFactory` | Centraliza criação de clientes (cacheados) e da cadeia |
| **Chain of Responsibility** | `ChatService` | Tenta provedores em ordem até um responder |
| **Dependency Injection** | `create_app` | Monta e injeta clientes/serviços |

---

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e Docker Compose
- Uma chave da **Groq** — https://console.groq.com/keys
- Uma chave do **Gemini** (para o fallback) — https://aistudio.google.com/apikey

---

## Configuração

Copie o exemplo e preencha as chaves:

```bash
cp .env.example .env
```

Variáveis (`.env`):

| Variável | Obrigatória | Descrição |
|---|---|---|
| `CHAT_API_KEY` | sim | Chave da Groq usada por chat/STT/OCR (alias: `GROQ_API_KEY`) |
| `STT_API_KEY` | sim | Chave da Groq para transcrição |
| `OCR_API_KEY` | sim | Chave da Groq para OCR |
| `GROQ_MODEL` | não | Modelo de chat do Groq (padrão `llama-3.3-70b-versatile`) |
| `GEMINI_API_KEY` | não* | Chave do Gemini (ativa o fallback de chat) |
| `GEMINI_MODEL` | não | Modelo do Gemini (padrão `gemini-2.5-flash`) |
| `PORT` | não | Porta do serviço (padrão `5000`) |

\* Sem `GEMINI_API_KEY` o serviço funciona só com o provedor que tiver chave.
A ordem de prioridade do chat é **Gemini → Groq**.

---

## Como rodar

### Com Docker (recomendado)

O Compose conecta o serviço a uma rede externa chamada `net1` (compartilhada com
os outros serviços do sistema). Crie-a se ainda não existir:

```bash
docker network create net1   # ignore o erro se já existir

docker compose up --build
```

O serviço sobe em `http://localhost:5000`.

> **Atenção (desenvolvimento):** o `Dockerfile` roda a aplicação a partir de
> `/home/app` (código copiado na imagem). Portanto, **alterações em código Python
> exigem rebuild**: `docker compose up -d --build`. Alterações apenas no `.env`
> precisam só recriar o container: `docker compose up -d --force-recreate`.

### Localmente (sem Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## Endpoints

Base URL: `http://localhost:5000`

### `GET /ai/health`
Healthcheck.
```json
{ "status": "ok" }
```

### `POST /chat/completions`
Chat com suporte opcional a *tool calling*.

**Request**
```json
{
  "systemPrompt": "Você é a Sophia, assistente da farmácia.",
  "messages": [
    { "role": "user", "content": "Vocês têm dipirona?" }
  ],
  "tools": [
    {
      "definition": {
        "name": "buscar_produto",
        "description": "Busca um produto no estoque",
        "inputSchema": {
          "type": "object",
          "properties": { "nome": { "type": "string" } },
          "required": ["nome"]
        }
      }
    }
  ]
}
```

**Response**
```json
{
  "text": "Deixa eu verificar...",
  "toolCalls": [
    { "toolUseId": "call_abc", "name": "buscar_produto", "args": { "nome": "dipirona" } }
  ]
}
```

Exemplo com `curl`:
```bash
curl -X POST http://localhost:5000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"diga oi"}]}'
```

### `POST /stt/transcribe`
Transcreve um arquivo de áudio (multipart `file`).
```bash
curl -X POST http://localhost:5000/stt/transcribe -F "file=@audio.ogg"
```
```json
{ "text": "texto transcrito" }
```

### `POST /ocr/read`
Extrai medicamentos de uma imagem de receita (multipart `file`).
```bash
curl -X POST http://localhost:5000/ocr/read -F "file=@receita.jpg"
```
```json
{ "medications": [ { "medication_name": "...", "dosage": "...", "...": "..." } ] }
```

---

## Notas

- O serviço de **TTS** (síntese de voz) foi removido do projeto.
- **Fallback:** o `ChatService` tenta os provedores em ordem e só retorna erro
  `500` se **todos** falharem; cada falha intermediária é registrada em log.
