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

Total pe disc: ~53 GB

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
| `cc-gemini` | gemini-2.5-flash | LiteLLM → Google |
| `cc-glm-coding` | glm-coding | LiteLLM → Z.ai |
| `cc-glm-credits` | glm-credits | LiteLLM → Z.ai |
| `cc-z` | glm-z | LiteLLM → Z.ai |

## RTK (Token Killer)

- Binary: `~/.local/bin/rtk` (via pipx)
- Auto-rewrite comenzi Bash prin hook Claude Code
- Wrappers în zshrc: `python3`, `python` → `rtk proxy`, `jq` → `rtk jq`

## Cum pornești LiteLLM

```bash
source ~/venv-litellm/bin/activate
litellm --config ~/config.yaml
```

## Cum folosești un model local

```bash
cc-mistral          # deschide Claude Code cu mistral-small3.2:24b
cc-deepseek         # deepseek-r1:32b
cc-glm-local        # glm-4.7-flash
```

Sau direct cu model arbitrar prin LiteLLM:
```bash
ccl --model mistral-small
```
