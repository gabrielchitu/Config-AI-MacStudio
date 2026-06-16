# Demo Roadmap — Local LLM Testing

## Varianta A — ✅ FUNCȚIONAL (group matching minimal)

**Scop:** Validare că un LLM local poate face matching semantic între grupuri de devize cu formate diferite.

**Status:** ✅ Funcțional — testat 2026-06-16, toate 3 modele locale, 3/3 grupuri matched corect

**Locație:** `demo/`

**Rulare:**
```bash
cd demo
# editezi MODEL in .env: mistral-small / deepseek-local / glm-local / gemini-2.5-flash
python3 run_demo.py
```

**Ce face:**
- Încarcă 3 devize din `test_data/referinta_mini.json` + `test_data/oferta_mini.json`
- Date reale din DT2 (Drum Tatarani): ref cu format `0001 Terasamente 7,70smp`, oferta cu `ZO0001 Terasamente 7.70 smp`
- Apelează LLM via `AnthropicAdapter` → `anthropic` SDK → LiteLLM → Ollama
- Printează perechile găsite + timp de răspuns

**Fișiere:**
- `demo/run_demo.py` — entry point
- `demo/anthropic_adapter.py` — bridge OpenAI-compatible → Anthropic SDK
- `demo/test_data/referinta_mini.json` — 3 devize referință DT2
- `demo/test_data/oferta_mini.json` — 3 devize ofertă DT2 (ordine amestecată)
- `demo/.env` — MODEL + ANTHROPIC_BASE_URL + ANTHROPIC_API_KEY

**Switch model:** editezi un rând în `.env`

### Benchmark Varianta A (3 grupuri DT2)

| Model | Score | Timp/call | Note |
|---|---|---|---|
| mistral-small3.2:24b | 3/3 ✅ | 24.0s | via LiteLLM |
| deepseek-r1:32b | 3/3 ✅ | 62.4s | via LiteLLM |
| glm-4.7-flash | 3/3 ✅ | 40.4s | Ollama direct (bypass LiteLLM — template non-chat) |

> **GLM gotcha:** `glm-4.7-flash:latest` are template `{{ .Prompt }}` (non-chat). LiteLLM streaming parse eșuează silențios → content gol. Fix: bypass LiteLLM, POST direct la Ollama `/api/generate`. Implementat în `run_demo.py` via `_OLLAMA_DIRECT_MAP`.

---

## Varianta B — ✅ FUNCȚIONAL (pipeline complet DT2)

**Scop:** Pipeline end-to-end real pe DT2 (189 grupuri) cu model local.

**Status:** ✅ Funcțional — testat 2026-06-16, mistral-small, rezultate identice cu claude-sonnet baseline

**Locație:** `demo/pipeline/`

**Rulare:**
```bash
cd demo/pipeline
python3 run_pipeline.py
# sau cu model/ofertă specifice:
MODEL=deepseek-local OFERTA_NR=2 python3 run_pipeline.py
```

**Ce face:**
- Adaugă `analiza-oferte-local` la `sys.path` (nu copiază fișiere — reutilizează `shared/` direct)
- Reutilizează checkpoints DT2 existente (sare clasificarea LLM de pagini — deja făcută)
- Rulează: extragere articole → normalizare devize → compare_by_groups → build_raport_holistic
- Output: `demo/pipeline/output/holistic_oferta_N_MODEL_TIMESTAMP.json`

**Fișiere:**
- `demo/pipeline/run_pipeline.py` — entry point
- `demo/pipeline/output/` — JSON-uri generate
- `demo/.env` — MODEL + ANTHROPIC_BASE_URL (shared cu Varianta A)

### Benchmark Varianta B (189 grupuri DT2, oferta_1)

| Model | Grupuri matched | Articole matched | NC total | Timp total |
|---|---|---|---|---|
| mistral-small3.2:24b | 189/189 ✅ | 1548 | 788 | 17.8s |
| claude-sonnet-4-6 (baseline) | 189/189 ✅ | 1547 | 788 | ~120s |

mistral-small local ≈ identic cu claude-sonnet: aceleași grupuri, același număr NC, +1 articol matched. Cost: 0 credite. Viteză: 6.7× mai rapid.

### Baseline de comparat

`analiza-oferte-local/output_AO/DT2/holistic_oferta_1.json` (rulat cu claude-sonnet-4-6):
- 189/189 grupuri matched
- 1547 articole matched, 788 NC
