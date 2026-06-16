"""
Demo: group matching cu LLM local via LiteLLM.

Switch model: editeaza MODEL in .env
  MODEL=mistral-small      → mistral-small3.2:24b (Ollama)
  MODEL=deepseek-local     → deepseek-r1:32b (Ollama)
  MODEL=glm-local          → glm-4.7-flash (Ollama)
  MODEL=gemini-2.5-flash   → Gemini cloud (via LiteLLM)

Rulare:
  cd demo && python3 run_demo.py
"""
import json
import os
import time
import logging
from pathlib import Path

import re
import httpx
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).parent / ".env")

MODEL = os.environ["MODEL"]
BASE_URL = os.environ["ANTHROPIC_BASE_URL"]
API_KEY = os.environ["ANTHROPIC_API_KEY"]
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

# Modele care necesită bypass LiteLLM → Ollama direct (template {{ .Prompt }}, non-chat)
_OLLAMA_DIRECT_MAP = {
    "glm-local": "glm-4.7-flash:latest",
}

DATA_DIR = Path(__file__).parent / "test_data"

_LLM_GROUP_SYSTEM_PROMPT = (
    "Ești expert în devize de construcții românești.\n"
    "Mai jos sunt grupuri din REFERINȚĂ și OFERTĂ care nu s-au potrivit automat.\n"
    "Textele pot fi abreviate diferit pentru aceeași categorie. "
    "Pot fi de lungimi diferite, în schimb înseamnă același obiectiv sau obiect "
    "sau categorie de lucrări / stadiu fizic.\n\n"
    'Returnează JSON cu cheia "matches":\n'
    '{"matches": [{"ref": "<ref_den_exact>", "oferta": "<oferta_den_exact>"}]}\n\n'
    "Omite perechile nesigure. Dacă nu există nicio potrivire clară, returnează "
    '{"matches": []}.'
)


def _den_string(hdr: dict) -> str:
    parts = [hdr.get("obiectivul"), hdr.get("obiectul"), hdr.get("categoria")]
    return " | ".join(p for p in parts if p)


def load_headers(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)["deviz_headers"]


def llm_call(model: str, system: str, user: str) -> str:
    """Apel LLM. GLM→Ollama direct (non-chat template). Restul→LiteLLM /v1/chat/completions."""
    if model in _OLLAMA_DIRECT_MAP:
        return _llm_call_ollama_direct(model, system, user)
    payload = {
        "model": model,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": system + "\nReturn ONLY valid JSON. No markdown, no explanation."},
            {"role": "user", "content": user},
        ],
        "max_tokens": 1000,
    }
    r = httpx.post(
        f"{BASE_URL}/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=120.0,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _llm_call_ollama_direct(model: str, system: str, user: str) -> str:
    """Bypass LiteLLM — cheamă Ollama /api/generate direct (pentru modele non-chat template)."""
    ollama_model = _OLLAMA_DIRECT_MAP[model]
    prompt = f"{system}\nReturn ONLY valid JSON. No markdown, no explanation.\n\nUSER:\n{user}"
    r = httpx.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": ollama_model, "prompt": prompt, "stream": False, "options": {"temperature": 0}},
        timeout=180.0,
    )
    r.raise_for_status()
    return r.json()["response"]


def run_match(ref_headers: dict, oferta_headers: dict) -> list:
    ref_den_to_key = {_den_string(v): k for k, v in ref_headers.items() if _den_string(v)}
    oferta_den_to_key = {_den_string(v): k for k, v in oferta_headers.items() if _den_string(v)}

    ref_list = "\n".join(f'{i+1}. "{d}"' for i, d in enumerate(ref_den_to_key))
    oferta_list = "\n".join(f'{i+1}. "{d}"' for i, d in enumerate(oferta_den_to_key))

    user_prompt = (
        f"REFERINȚĂ (grupuri nematched):\n{ref_list}\n\n"
        f"OFERTĂ (grupuri nematched):\n{oferta_list}"
    )

    endpoint = f"{OLLAMA_HOST}/api/generate" if MODEL in _OLLAMA_DIRECT_MAP else f"{BASE_URL}/v1/chat/completions"
    logger.info(f"Calling LLM: {MODEL} @ {endpoint}")
    t0 = time.time()

    raw = llm_call(MODEL, _LLM_GROUP_SYSTEM_PROMPT, user_prompt)
    elapsed = time.time() - t0

    logger.info(f"Raw response: {raw!r}")

    # strip markdown fences dacă modelul le adaugă
    if raw:
        m = re.search(r'```(?:json)?\s*([\s\S]+?)\s*(?:```|$)', raw)
        if m:
            raw = m.group(1)

    parsed = json.loads(raw) if raw else {}
    matches = parsed.get("matches", [])

    results = []
    for m in matches:
        ref_den = m.get("ref", "")
        oferta_den = m.get("oferta", "")
        ref_key = ref_den_to_key.get(ref_den, "?")
        oferta_key = oferta_den_to_key.get(oferta_den, "?")
        results.append({
            "ref_key": ref_key,
            "oferta_key": oferta_key,
            "ref_den": ref_den,
            "oferta_den": oferta_den,
        })

    return results, elapsed


def main():
    print(f"\n{'='*60}")
    print(f"  Model:    {MODEL}")
    print(f"  Endpoint: {BASE_URL}")
    print(f"{'='*60}\n")

    ref_headers = load_headers(DATA_DIR / "referinta_mini.json")
    oferta_headers = load_headers(DATA_DIR / "oferta_mini.json")

    print(f"REFERINȚĂ ({len(ref_headers)} grupuri):")
    for k, v in ref_headers.items():
        print(f"  [{k[:8]}] {_den_string(v)}")

    print(f"\nOFERTĂ ({len(oferta_headers)} grupuri, ordine amestecată):")
    for k, v in oferta_headers.items():
        print(f"  [{k[:8]}] {_den_string(v)}")

    print(f"\nRulez matching LLM...")
    try:
        matches, elapsed = run_match(ref_headers, oferta_headers)
    except Exception as e:
        print(f"\nERROR: {e}")
        raise

    print(f"\nREZULTAT ({len(matches)} perechi găsite, {elapsed:.1f}s):\n")
    if not matches:
        print("  Nicio pereche găsită.")
    for i, m in enumerate(matches, 1):
        ref_short = m["ref_den"].split(" | ")[-1]
        oferta_short = m["oferta_den"].split(" | ")[-1]
        status = "✓" if m["ref_key"] != "?" and m["oferta_key"] != "?" else "?"
        print(f"  {status} {i}. REF: {ref_short}")
        print(f"       OF:  {oferta_short}")
        print()

    correct = sum(1 for m in matches if m["ref_key"] != "?" and m["oferta_key"] != "?")
    print(f"Score: {correct}/{len(ref_headers)} grupuri matched corect din {len(ref_headers)} posibile")
    print(f"Model: {MODEL} | Timp: {elapsed:.1f}s\n")


if __name__ == "__main__":
    main()
