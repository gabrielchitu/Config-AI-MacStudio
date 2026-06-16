# LiteLLM — Configurație și Setup

## Overview

LiteLLM Router rulează local ca proxy Anthropic-compatible — permite Claude Code să folosească orice model (Ollama, Gemini, Z.ai) prin același protocol.

```
Claude Code  →  localhost:4000 (LiteLLM)  →  Ollama / Google / Z.ai
               (Anthropic API protocol)
```

## Versiuni

| Component | Versiune |
|---|---|
| LiteLLM | `1.48.19` |
| Ollama | `0.20.3` |
| Venv | `~/venv-litellm/` |

## Config principal

Fișier: `~/config.yaml`

```yaml
general_settings:
  master_key: "os.environ/LITELLM_MASTER_KEY"   # sk-local-... din LITELLM_MASTER_KEY env
  host: "0.0.0.0"
  port: 4000

litellm_settings:
  drop_params: true       # ignoră params necunoscuți (compatibilitate)
  request_timeout: 600    # 10 min — necesar pentru modele mari locale

router_settings:
  num_retries: 1
  timeout: 120
```

## Model list

### Local — Ollama (localhost:11434)

| model_name | Ollama model | Size |
|---|---|---|
| `mistral-small` | `mistral-small3.2:24b` | 15 GB |
| `deepseek-local` | `deepseek-r1:32b` | 19 GB |
| `glm-local` | `glm-4.7-flash:latest` | 19 GB |

Toți cu `custom_llm_provider: anthropic` — LiteLLM traduce protocolul Ollama → Anthropic.

### Cloud — Gemini

| model_name | Model real | API |
|---|---|---|
| `gemini-2.5-flash` | `openai/gemini-2.5-flash` | `generativelanguage.googleapis.com/v1beta/openai/` |

Cheie: `GEMINI_API_KEY` din env.

### Cloud — Z.ai GLM-4.7

| model_name | Endpoint | Tip |
|---|---|---|
| `glm-coding` | `/api/coding/paas/v4` | abonament coding |
| `glm-credits` | `/api/paas/v4` | prepay credits |

Ambele folosesc `openai/glm-4.7` + `ZAI_API_KEY` din env.

---

## Ollama — Autostart (launchd)

Ollama pornește automat la login via Homebrew LaunchAgent.

Fișier: `~/Library/LaunchAgents/homebrew.mxcl.ollama.plist`

Configurație relevantă:
```xml
<key>OLLAMA_HOST</key>       <string>0.0.0.0</string>        <!-- ascultă pe toate interfețele -->
<key>OLLAMA_FLASH_ATTENTION</key>  <string>1</string>         <!-- optimizare memorie -->
<key>OLLAMA_KV_CACHE_TYPE</key>    <string>q8_0</string>      <!-- cache quantizat 8-bit -->
```

- Log: `/opt/homebrew/var/log/ollama.log`
- `KeepAlive: true` — repornește automat dacă cade
- `RunAtLoad: true` — pornește la login

## LiteLLM — Start manual

LiteLLM **nu are autostart** — se pornește manual:

```bash
source ~/venv-litellm/bin/activate
litellm --config ~/config.yaml
```

Log-uri: `~/litellm.log` și `~/litellm.error.log`

### Verificare că rulează

```bash
curl http://localhost:4000/health
curl http://localhost:4000/v1/models
```

### Test model local

```bash
# Via Claude Code alias
cc-mistral

# Via curl direct
curl http://localhost:4000/v1/messages \
  -H "x-api-key: $LITELLM_MASTER_KEY" \
  -H "content-type: application/json" \
  -d '{"model":"mistral-small","max_tokens":100,"messages":[{"role":"user","content":"test"}]}'
```

---

## Variabile env necesare

| Var | Folosit pentru |
|---|---|
| `LITELLM_MASTER_KEY` | Autentificare client → LiteLLM |
| `GEMINI_API_KEY` | Model `gemini-2.5-flash` |
| `ZAI_API_KEY` | Modele `glm-coding`, `glm-credits` |

> Toate cheile sunt setate în shell env (nu în config.yaml în clar).

---

## Troubleshooting

**LiteLLM nu răspunde:**
```bash
lsof -i :4000          # verifică dacă portul e ocupat
cat ~/litellm.error.log | tail -50
```

**Ollama nu răspunde:**
```bash
curl http://localhost:11434/api/tags    # listează modele
ollama ps                               # modele încărcate în RAM
brew services restart ollama
```

**Model lent la prima rulare:**  
Normal — Ollama încarcă modelul în RAM (15-19 GB). Primul request poate dura 30-60s.
