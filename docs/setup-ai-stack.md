# AI Stack — MacStudio

## Arhitectură

```
Claude Code CLI
     │
     ├── Anthropic direct (OAuth / API key)
     │
     └── LiteLLM Router (localhost:4000)
              │
              ├── Ollama (localhost:11434) — modele locale
              │        ├── mistral-small3.2:24b
              │        ├── deepseek-r1:32b
              │        └── glm-4.7-flash:latest
              │
              ├── Gemini 2.5 Flash (Google API)
              │
              └── Z.ai GLM-4.7 (cloud — coding + credits)
```

## LiteLLM

- Config: `~/config.yaml`
- Port: `4000`
- Master key: `LITELLM_MASTER_KEY` (din env)
- Venv: `~/venv-litellm/`

### Model aliases (LiteLLM → backend)

| model_name | backend | provider |
|---|---|---|
| `mistral-small` | `ollama/mistral-small3.2:24b` | local |
| `deepseek-local` | `ollama/deepseek-r1:32b` | local |
| `glm-local` | `ollama/glm-4.7-flash:latest` | local |
| `qwen-coder` | `ollama/qwen2.5-coder:14b` | local |
| `gemini-2.5-flash` | Google Generative Language API | cloud |
| `glm-coding` | Z.ai `/api/coding/paas/v4` | cloud |
| `glm-credits` | Z.ai `/api/paas/v4` | cloud |

## Ollama

- Versiune: `0.20.3`
- Port: `11434`
- Modele instalate:

| Model | Size | Tag |
|---|---|---|
| mistral-small3.2 | 15 GB | `24b` |
| deepseek-r1 | 19 GB | `32b` |
| glm-4.7-flash | 19 GB | `latest` |
| glm-4.7 | — | `cloud` (fără weights) |
| qwen2.5-coder | 9 GB | `14b` |

Total pe disc: ~62 GB

## Claude Code aliases (zshrc)

| Alias | Model | Rută |
|---|---|---|
| `cc` | claude (subscription) | Anthropic OAuth direct |
| `ccs` | claude-sonnet-4-6 | Anthropic direct |
| `cco` | claude-opus-4-6 | Anthropic direct |
| `ccl` | orice model | LiteLLM localhost:4000 |
| `cc-mistral` | mistral-small | LiteLLM → Ollama |
| `cc-deepseek` | deepseek-local | LiteLLM → Ollama |
| `cc-glm-local` | glm-local | LiteLLM → Ollama |
| `cc-qwen` | qwen-coder | LiteLLM → Ollama |
| `cc-gemini` | gemini-2.5-flash | LiteLLM → Google |
| `cc-glm-coding` | glm-coding | LiteLLM → Z.ai |
| `cc-glm-credits` | glm-credits | LiteLLM → Z.ai |
| `cc-z` | glm-z | LiteLLM → Z.ai |

## RTK (Token Killer)

- Binary: `~/.local/bin/rtk` (via pipx)
- Auto-rewrite comenzi Bash prin hook Claude Code
- Wrappers în zshrc: `python3`, `python` → `rtk proxy`, `jq` → `rtk jq`

## LiteLLM — Autostart (LaunchDaemon)

LiteLLM pornește automat la boot via LaunchDaemon (ca `root`):

- Fișier: `/Library/LaunchDaemons/com.gabrielchitu.litellm.plist`
- Port: **4000** (stabil — KeepAlive: true)
- Auth key: `sk-local-7279bbc34c1ec9e2b37e1e15e941f820` (virtual key, DB mode)
- Log: `~/litellm.log` și `~/litellm.error.log` (owned root)

**Restart după modificare config.yaml:**
```bash
sudo launchctl unload /Library/LaunchDaemons/com.gabrielchitu.litellm.plist
sudo launchctl load /Library/LaunchDaemons/com.gabrielchitu.litellm.plist
```

> NU porni LiteLLM manual — daemonul ocupă portul 4000, instanța manuală alege port random.

## Cum folosești un model local

```bash
cc-mistral          # deschide Claude Code cu mistral-small3.2:24b
cc-deepseek         # deepseek-r1:32b
cc-glm-local        # glm-4.7-flash
cc-qwen             # qwen2.5-coder:14b
```

Sau direct cu model arbitrar prin LiteLLM:
```bash
ccl --model mistral-small
```

## Integrare analiza-oferte-local

Pipeline-ul real suportă local LLM via `.env`:

```env
ANTHROPIC_BASE_URL=http://localhost:4000
ANTHROPIC_API_KEY=sk-local-7279bbc34c1ec9e2b37e1e15e941f820
ANTHROPIC_MODEL=mistral-small   # sau qwen-coder / deepseek-local
```

Switch înapoi la Anthropic: comentezi `ANTHROPIC_BASE_URL` + pui `ANTHROPIC_API_KEY=sk-ant-...`.

Rulare pipeline cu local LLM:
```bash
cd ~/analiza-oferte-local
python3 multi_client_run.py --client DT2
```
