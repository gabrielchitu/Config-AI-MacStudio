# zshrc — Documentație completă

Fișier: `~/.zshrc`

## PATH & Env

```zsh
export PATH="$PATH:/Users/gabrielchitu/.local/bin"   # pipx binaries (rtk, litellm etc.)
export LITELLM_MASTER_KEY=<din env>                   # cheie router LiteLLM localhost:4000
```

> `ANTHROPIC_API_KEY` **nu e exportat global** — fiecare alias local îl injectează explicit.

---

## Claude Code Aliases

### Anthropic direct (OAuth / subscription)

```zsh
alias cc='claude'                          # model default (subscription)
alias ccs='claude --model claude-sonnet-4-6'
alias cco='claude --model claude-opus-4-6'
```

### LiteLLM router (localhost:4000)

Toate alias-urile de mai jos injectează:
```
ANTHROPIC_BASE_URL=http://localhost:4000
ANTHROPIC_API_KEY=sk-local-<cheie proxy>
```

**Funcție helper comună:**
```zsh
_cc_llm() {
  ANTHROPIC_BASE_URL=http://localhost:4000 \
    ANTHROPIC_API_KEY=<proxy key> \
    claude --model "$1" "${@:2}"
}
```

#### Modele locale (Ollama via LiteLLM)

| Alias | model_name LiteLLM | Backend Ollama |
|---|---|---|
| `cc-mistral` | `mistral-small` | `mistral-small3.2:24b` |
| `cc-deepseek` | `deepseek-local` | `deepseek-r1:32b` |
| `cc-glm-local` | `glm-local` | `glm-4.7-flash:latest` |
| `cc-qwen` | `qwen-coder` | `qwen2.5-coder:14b` |

#### Modele cloud (via LiteLLM)

| Alias | model_name LiteLLM | Provider real |
|---|---|---|
| `cc-gemini` | `gemini-2.5-flash` | Google Generative Language API |
| `cc-glm-coding` | `glm-coding` | Z.ai `/api/coding/paas/v4` |
| `cc-glm-credits` | `glm-credits` | Z.ai `/api/paas/v4` |
| `cc-z` | `glm-z` | Z.ai (funcție `_cc_z`) |
| `ccl` | orice model | LiteLLM (alias generic) |

#### Alias-uri legacy (definite anterior, încă active)

```zsh
alias cc-coder='_cc_local coder'      # → model "coder" (mistral-small:3.2)
alias cc-coding='_cc_local coding'    # → model "coding" (mistral-small:3.2)
alias cc-reason='_cc_local reasoning' # → model "reasoning" (deepseek-r1:32b)
```

> Folosesc `_cc_local` (funcție identică cu `_cc_llm`, definită mai devreme în fișier).

---

## RTK Wrappers

Adăugate **2026-05-18** pentru optimizare token (~175K tokens savings potențial).

```zsh
alias python3='rtk proxy python3'   # 1,680 apeluri identificate în history
alias python='rtk proxy python'
alias jq='rtk jq'                   # ~10K tokens saved per sesiune
alias stat='rtk run stat'
# alias cat='rtk read'              # dezactivat — probleme interactive
# alias git='rtk git'               # dezactivat — RTK hook deja gestionează
```

`rtk proxy` — execută comanda fără filtrare dar trackează usage-ul.

---

## Session Compression Monitor

Adăugat **2026-05-18**. Funcție `_session_progress()` — progress bar vizual pentru compresia contextului Claude.

```zsh
alias caveman='_session_progress'   # rulează manual
# Auto-run la fiecare shell startup
_session_progress
```

**Cum funcționează:**
- Citește dimensiunea fișierului `.jsonl` al sesiunii curente
- Threshold estimat: 200KB (~150-200KB în practică, variază per model)
- Afișează bara colorată: verde < 75%, galben 75-99%, roșu 100%

**Limitare:** Calea sesiunii e hardcodată (`analiza-oferte-local/773c56b5-...jsonl`).  
La schimbarea proiectului activ, funcția raportează "sesiune negăsită".

---

## Ordine definire (rezumat)

```
1. PATH + env vars
2. Claude Code aliases simple (cc, ccs, cco, ccl, cc-z, _cc_local)
3. alias cc-coder/coding/reason (via _cc_local)
4. RTK wrappers (python3, python, jq, stat)
5. _cc_llm + aliases multi-provider (cc-mistral, cc-deepseek etc.) — redefine cc
6. _session_progress + alias caveman + auto-run
```

> `alias cc='claude'` e definit de **două ori** (pct. 2 și 5) — al doilea suprascrie primul, rezultat identic.

---

## LiteLLM — Daemon (autostart)

LiteLLM pornește automat la boot — **nu se pornește manual**.

```zsh
# Restart după modificare ~/config.yaml
sudo launchctl unload /Library/LaunchDaemons/com.gabrielchitu.litellm.plist
sudo launchctl load  /Library/LaunchDaemons/com.gabrielchitu.litellm.plist

# Verificare
curl http://localhost:4000/v1/models -H "Authorization: Bearer sk-local-7279bbc34c1ec9e2b37e1e15e941f820"
```

> Auth key pentru CLI + scripturi: `sk-local-7279bbc34c1ec9e2b37e1e15e941f820` (virtual key, DB mode).  
> `gabriel2026` funcționează doar la instanțe manuale fără daemon.

---

## Comenzi rapide referință

```zsh
# Token savings analytics
rtk gain
rtk gain --history

# Session compression status
caveman   # sau direct: _session_progress

# Modele locale
cc-mistral    # mistral-small3.2:24b
cc-deepseek   # deepseek-r1:32b
cc-qwen       # qwen2.5-coder:14b
cc-glm-local  # glm-4.7-flash
```
