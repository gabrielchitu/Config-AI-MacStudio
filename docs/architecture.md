# Arhitectură — Local AI Stack MacStudio

## Overview

Stack-ul permite rularea oricărui LLM local (Ollama) sau cloud (Gemini, Z.ai) ca înlocuitor drop-in pentru Anthropic API. Claude Code și scripturile Python nu știu cu ce model vorbesc — schimbi un env var.

---

## Diagrama completă

```
┌─────────────────────────────────────────────────────────┐
│                     CLIENȚI                             │
│                                                         │
│  Claude Code CLI          Python scripts (demo/)        │
│  (cc-mistral alias)       (run_demo.py)                 │
│         │                        │                      │
│  ANTHROPIC_BASE_URL       ANTHROPIC_BASE_URL            │
│  = localhost:4000         = localhost:PORT              │
│  ANTHROPIC_API_KEY        ANTHROPIC_API_KEY             │
│  = sk-local-...           = gabriel2026                 │
└──────────────┬───────────────────┬─────────────────────┘
               │                   │
               ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│              LiteLLM Router (~/config.yaml)             │
│              port: 4000 (sau random dacă ocupat)        │
│              master_key: gabriel2026                    │
│                                                         │
│  /v1/messages      ← Anthropic SDK (AnthropicAdapter)  │
│  /v1/chat/completions ← httpx direct / OpenAI SDK      │
│                                                         │
│  Model routing:                                         │
│  "mistral-small"    → ollama/mistral-small3.2:24b      │
│  "deepseek-local"   → ollama/deepseek-r1:32b           │
│  "glm-local"        → ollama/glm-4.7-flash:latest      │
│  "gemini-2.5-flash" → Google Generative Language API   │
│  "glm-coding"       → Z.ai /api/coding/paas/v4         │
│  "glm-credits"      → Z.ai /api/paas/v4                │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Ollama (localhost:11434)    │
│  Autostart: LaunchAgent      │
│  OLLAMA_FLASH_ATTENTION=1    │
│  OLLAMA_KV_CACHE_TYPE=q8_0   │
│                              │
│  mistral-small3.2:24b  15GB  │
│  deepseek-r1:32b       19GB  │
│  glm-4.7-flash:latest  19GB  │
└──────────────────────────────┘
```

---

## Protocol flow — Python demo

```
run_demo.py
  load .env → MODEL, ANTHROPIC_BASE_URL, ANTHROPIC_API_KEY
  httpx.post(BASE_URL + "/v1/chat/completions")
    Authorization: Bearer gabriel2026
    body: {model: "mistral-small", messages: [...]}
         ↓
  LiteLLM primește request OpenAI-format
  mapează "mistral-small" → ollama/mistral-small3.2:24b
  trimite la Ollama localhost:11434
         ↓
  Ollama rulează modelul local
  răspunde cu text
         ↓
  LiteLLM returnează response OpenAI-format
  run_demo.py parsează JSON din răspuns (cu strip markdown fences)
```

## Protocol flow — Claude Code aliases

```
cc-mistral (zshrc alias)
  setează ANTHROPIC_BASE_URL=localhost:4000
  setează ANTHROPIC_API_KEY=sk-local-...  (virtual key cu DB)
  lansează claude CLI
         ↓
  Claude Code trimite Anthropic-format requests la localhost:4000
  LiteLLM routează la Ollama
  Răspunsul vine înapoi ca și cum ar fi claude-sonnet
```

---

## Gotchas cunoscute

| Problemă | Cauză | Fix |
|---|---|---|
| `custom_llm_provider: anthropic` pe Ollama | LiteLLM încearcă Anthropic API | Scoate din config.yaml pentru modele Ollama |
| `response_format: json_object` → 500 | Bug în litellm/llms/ollama.py | Nu trimite response_format; strip fences manual |
| `sk-local-...` → 401 pe instanță nouă | Virtual keys cer DB conectat | Folosește master key `gabriel2026` |
| Port 4000 ocupat | Alt proces pe port | LiteLLM pornește pe port random; actualizează .env |
| Model returnează markdown fences | Comportament implicit modele | Strip cu regex înainte de json.loads() |

---

## Switch model (demo)

Editezi `demo/.env`:
```env
MODEL=mistral-small      # 15GB, 14s/call
MODEL=deepseek-local     # 19GB, ~30-60s/call (cold start)
MODEL=glm-local          # 19GB, ~?s
MODEL=gemini-2.5-flash   # cloud, ~2-3s
```

Codul `run_demo.py` nu se schimbă.

---

## Benchmark rezultate

| Model | Score | Timp/call | Date |
|---|---|---|---|
| mistral-small3.2:24b | 3/3 ✅ | 14.2s | 2026-06-16 |
| deepseek-r1:32b | - | - | netestat |
| glm-4.7-flash | - | - | netestat |

Baseline Anthropic (claude-sonnet-4-6): 189/189 grupuri DT2, ~2s/call.
