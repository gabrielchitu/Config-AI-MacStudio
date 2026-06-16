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
│  "glm-local"        → ollama/glm-4.7-flash:latest
  "qwen-coder"       → ollama/qwen2.5-coder:14b      │
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
│  qwen2.5-coder:14b      9GB  │
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
| `glm-4.7-flash` via LiteLLM → content gol | Template `{{ .Prompt }}` non-chat; LiteLLM streaming parse eșuează | Bypass LiteLLM → Ollama `/api/generate` direct (`_OLLAMA_DIRECT_MAP` în run_demo.py) |

---

## Switch model (demo)

Editezi `demo/.env`:
```env
MODEL=mistral-small      # 15GB, 14s/call
MODEL=deepseek-local     # 19GB, ~30-60s/call (cold start)
MODEL=glm-local          # 19GB, 40s (Ollama direct, bypass LiteLLM)
MODEL=gemini-2.5-flash   # cloud, ~2-3s
```

Codul `run_demo.py` nu se schimbă.

---

## Benchmark rezultate

### Varianta A — group matching minimal (3 grupuri DT2)

| Model | Score | Timp/call | Date |
|---|---|---|---|
| mistral-small3.2:24b | 3/3 ✅ | 24.0s | 2026-06-16 |
| deepseek-r1:32b | 3/3 ✅ | 62.4s | 2026-06-16 |
| glm-4.7-flash | 3/3 ✅ | 40.4s | 2026-06-16 |

### Varianta B — pipeline complet DT2 (189 grupuri, oferta_1)

| Model | Grupuri matched | Articole matched | NC total | Timp total | Date |
|---|---|---|---|---|---|
| mistral-small3.2:24b | 189/189 ✅ | 1548 | 788 | 17.8s | 2026-06-16 |
| claude-sonnet-4-6 (baseline) | 189/189 ✅ | 1547 | 788 | ~120s | 2026-06-11 |

mistral-small local ≈ identic cu claude-sonnet pe DT2: aceleași grupuri, același număr NC, +1 articol matched.
Pipeline durează 17.8s (fără clasificare pagini — reutilizează checkpoints existente).
