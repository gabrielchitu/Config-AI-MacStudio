# Demo Roadmap — Local LLM Testing

## Varianta A — ACTIV (group matching minimal)

**Scop:** Validare că un LLM local poate face matching semantic între grupuri de devize cu formate diferite.

**Status:** ✅ Funcțional — testat 2026-06-16, mistral-small3.2:24b, 3/3 grupuri matched corect, 14.2s/call

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
- Apelează LLM via `AnthropicAdapter` → `anthropic` SDK → LiteLLM (localhost:4000) → Ollama
- Printează perechile găsite + timp de răspuns

**Fișiere:**
- `demo/run_demo.py` — entry point
- `demo/anthropic_adapter.py` — bridge OpenAI-compatible → Anthropic SDK (copiat din analiza-oferte)
- `demo/test_data/referinta_mini.json` — 3 devize referință DT2
- `demo/test_data/oferta_mini.json` — 3 devize ofertă DT2 (ordine amestecată)
- `demo/.env` — MODEL + ANTHROPIC_BASE_URL + ANTHROPIC_API_KEY

**Switch model:** editezi un rând în `.env`

---

## Varianta B — URMEAZĂ (pipeline complet)

**Scop:** Testare performanță LLM local pe pipeline end-to-end real (nu doar group matching).

**Pre-condiție:** Varianta A funcționează pe toate 3 modelele locale.

### Ce adaugă față de A

1. **Date reale complete** — nu 3 devize ci tot DT2 (~189 grupuri, 2 oferte)
2. **Pipeline complet copiat:**
   - `AgentComparator_local.py` — orchestrator matching Layer 1-2.5
   - `shared/comparator.py` — matching NR + COD_SIMILAR + denomination
   - `shared/group_comparator.py` — group matching cu LLM (deja testat în A)
   - `shared/f3_knowledge.py` — context DT2 pentru LLM
   - `shared/ocr_patterns_knowledge.json` — normalizare coduri
3. **Output structural** — `holistic_oferta_N.json` cu matched/ref_only/oferta_only
4. **Verificare automată** — rulare `verify_agent.py` după pipeline

### Structura propusă

```
demo/
├── pipeline/
│   ├── AgentComparator_local.py      # copiat + adaptat pentru .env model switch
│   ├── shared/
│   │   ├── comparator.py
│   │   ├── group_comparator.py
│   │   ├── f3_knowledge.py
│   │   └── ocr_patterns_knowledge.json
│   ├── input/
│   │   ├── referinta.json            # output_AO/DT2/checkpoints/di_referinta_deviz_mapping_*.json
│   │   └── oferta_1.json             # output_AO/DT2/checkpoints/di_oferta_1_deviz_mapping_*.json
│   ├── output/                       # holistic_oferta_1.json generat
│   └── run_pipeline.py               # entry point — incarca .env, ruleaza, verifica
```

### Metrici de evaluat per model

| Metric | Cum se măsoară |
|---|---|
| Grupuri matched corect | `matched_groups` din holistic vs. baseline Anthropic |
| Invariant violations | `verify_agent.py` — 0 CRITICAL/HIGH expected |
| Timp total | `time python3 run_pipeline.py` |
| Timp per LLM call | log din group_comparator |
| Cost zero | toate local, nu consumă credite |

### Baseline de comparat

Rezultatele din `analiza-oferte-local/output_AO/Drum Tatarani/holistic_oferta_1.json` (rulat cu claude-sonnet-4-6):
- 189/189 grupuri matched
- 0 invariant violations

### Pași de implementare

1. Copiaza fișierele din analiza-oferte în `demo/pipeline/shared/`
2. Adaptează `AgentComparator_local.py` să citească model din `.env` (nu hardcodat)
3. Creează `run_pipeline.py` — simplu wrapper care rulează matching end-to-end
4. Rulează pe fiecare model, compară cu baseline
5. Documentează rezultatele în `docs/benchmark-results.md`

### Avertismente

- `deepseek-r1:32b` și `glm-4.7-flash` pot fi mai lente (19 GB, cold start 30-60s)
- Pipeline complet pe 189 grupuri = N LLM calls → poate dura 5-30 min per model
- Unele module din `shared/` au dependențe (rapidfuzz, python-docx) — verifică cu `pip list`
