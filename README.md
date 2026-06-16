# Config-AI-MacStudio

Configurații și documentație pentru stack-ul AI local pe MacStudio.

## Stack

- **Claude Code** — CLI principal (Anthropic OAuth)
- **LiteLLM 1.48.19** — proxy router la localhost:4000, protocol Anthropic-compatible
- **Ollama 0.20.3** — runtime modele locale la localhost:11434
- **RTK** — token killer, optimizare automată comenzi Bash în Claude Code

## Modele disponibile

| Alias | Model | Locație |
|---|---|---|
| `cc` | claude (subscription) | Anthropic direct |
| `ccs` | claude-sonnet-4-6 | Anthropic direct |
| `cco` | claude-opus-4-6 | Anthropic direct |
| `cc-mistral` | mistral-small3.2:24b (15 GB) | Ollama local |
| `cc-deepseek` | deepseek-r1:32b (19 GB) | Ollama local |
| `cc-glm-local` | glm-4.7-flash (19 GB) | Ollama local |
| `cc-qwen` | qwen2.5-coder:14b (9 GB) | Ollama local |
| `cc-gemini` | gemini-2.5-flash | Google API |
| `cc-glm-coding` | glm-4.7 | Z.ai coding |
| `cc-glm-credits` | glm-4.7 | Z.ai credits |

## Start LiteLLM

```bash
source ~/venv-litellm/bin/activate
litellm --config ~/config.yaml
```

Ollama pornește automat la login (Homebrew LaunchAgent).

## Docs

- [`docs/setup-ai-stack.md`](docs/setup-ai-stack.md) — arhitectură completă stack
- [`docs/zshrc.md`](docs/zshrc.md) — toate alias-urile și configurația shell
- [`docs/litellm-config.md`](docs/litellm-config.md) — LiteLLM config, Ollama autostart, troubleshooting
- [`docs/architecture.md`](docs/architecture.md) — protocol flow, gotchas, benchmark rezultate
- [`docs/demo-roadmap.md`](docs/demo-roadmap.md) — demo group matching local LLM (Varianta A + B)
