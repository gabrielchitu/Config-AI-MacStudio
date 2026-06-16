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

from dotenv import load_dotenv
import anthropic

from anthropic_adapter import AnthropicAdapter

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).parent / ".env")

MODEL = os.environ["MODEL"]
BASE_URL = os.environ["ANTHROPIC_BASE_URL"]
API_KEY = os.environ["ANTHROPIC_API_KEY"]

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


def run_match(ref_headers: dict, oferta_headers: dict, llm_client, model: str) -> list:
    ref_den_to_key = {_den_string(v): k for k, v in ref_headers.items() if _den_string(v)}
    oferta_den_to_key = {_den_string(v): k for k, v in oferta_headers.items() if _den_string(v)}

    ref_list = "\n".join(f'{i+1}. "{d}"' for i, d in enumerate(ref_den_to_key))
    oferta_list = "\n".join(f'{i+1}. "{d}"' for i, d in enumerate(oferta_den_to_key))

    user_prompt = (
        f"REFERINȚĂ (grupuri nematched):\n{ref_list}\n\n"
        f"OFERTĂ (grupuri nematched):\n{oferta_list}"
    )

    logger.info(f"Calling LLM: {model} @ {BASE_URL}")
    t0 = time.time()

    resp = llm_client.chat.completions.create(
        model=model,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _LLM_GROUP_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
    )

    elapsed = time.time() - t0
    raw = resp.choices[0].message.content
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

    raw_client = anthropic.Anthropic(base_url=BASE_URL, api_key=API_KEY)
    llm_client = AnthropicAdapter(raw_client, model=MODEL)

    print(f"\nRulez matching LLM...")
    try:
        matches, elapsed = run_match(ref_headers, oferta_headers, llm_client, MODEL)
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
