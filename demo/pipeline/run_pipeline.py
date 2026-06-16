"""
run_pipeline.py — Varianta B: pipeline complet DT2 cu model local.

Reutilizează codul din analiza-oferte-local (shared/) via sys.path.
Nu copiază fișiere — referențiază direct checkpoints DT2 existente.

Rulare:
    cd demo/pipeline
    MODEL=mistral-small python3 run_pipeline.py
    MODEL=mistral-small OFERTA_NR=2 python3 run_pipeline.py

Output:
    demo/pipeline/output/holistic_oferta_1_mistral-small_TIMESTAMP.json
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# ── Paths ──────────────────────────────────────────────────────────────────────
DEMO_DIR = Path(__file__).parent.parent          # demo/
PIPELINE_DIR = Path(__file__).parent             # demo/pipeline/
AO_ROOT = Path("/Users/gabrielchitu/analiza-oferte-local")
CHECKPOINT_DIR = AO_ROOT / "output_AO" / "DT2" / "checkpoints"
OUTPUT_DIR = PIPELINE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# analiza-oferte-local pe sys.path → shared/ + anthropic_adapter disponibile
sys.path.insert(0, str(AO_ROOT))

# ── Config ─────────────────────────────────────────────────────────────────────
load_dotenv(DEMO_DIR / ".env")

MODEL = os.environ["MODEL"]
BASE_URL = os.environ["ANTHROPIC_BASE_URL"]
API_KEY = os.environ["ANTHROPIC_API_KEY"]
OFERTA_NR = int(os.environ.get("OFERTA_NR", "1"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def build_client():
    """AnthropicAdapter + anthropic SDK pointing la LiteLLM local."""
    import anthropic
    from anthropic_adapter import AnthropicAdapter

    raw = anthropic.Anthropic(base_url=BASE_URL, api_key=API_KEY)
    return AnthropicAdapter(raw, model=MODEL), MODEL


def load_articles(name: str) -> tuple[list, dict]:
    """
    Extrage articolele dintr-un document DT2 folosind checkpoint-urile existente.
    Sare peste clasificarea LLM (deja făcută).

    Returns: (articles, deviz_checkpoint_data)
    """
    from shared.f3_extractor import extract_articles_v3
    from shared.deviz_namer import populate_deviz_denominations

    page_files = sorted(CHECKPOINT_DIR.glob(f"{name}_page_classes_*.json"))
    if not page_files:
        raise FileNotFoundError(f"No page_classes checkpoint for '{name}' in {CHECKPOINT_DIR}")
    ckpt = json.loads(page_files[0].read_text(encoding="utf-8"))
    page_classes = ckpt.get("page_classes", [])

    deviz_files = sorted(CHECKPOINT_DIR.glob(f"{name}_deviz_mapping_*.json"))
    deviz_data = json.loads(deviz_files[0].read_text(encoding="utf-8")) if deviz_files else {}

    articles = extract_articles_v3(page_classes)
    articles = populate_deviz_denominations(articles)
    articles = [a for a in articles if a.get("cod", "").strip()]
    logger.info(f"  {name}: {len(articles)} articole")
    return articles, deviz_data


def build_headers(deviz_data: dict, articles: list) -> dict:
    """Reconstruiește DevizHeader-urile din checkpoint_data."""
    from shared.deviz_header_extractor import DevizHeader

    headers: dict = {}
    if "deviz_headers" in deviz_data:
        for ck, hdr_data in deviz_data["deviz_headers"].items():
            hdr = DevizHeader(
                obiectivul=hdr_data.get("obiectivul"),
                obiectul=hdr_data.get("obiectul"),
                categoria=hdr_data.get("categoria"),
                deviz_key=hdr_data.get("deviz_key", ""),
                is_valid=hdr_data.get("is_valid", False),
                source="checkpoint",
                deviz_cod=hdr_data.get("deviz_cod", ck),
            )
            deviz_key = hdr_data.get("deviz_key", "") or ck
            if deviz_key:
                headers[deviz_key] = hdr
    else:
        # Fallback: reconstruct from article metadata
        from local_run import _headers_from_articles
        headers = _headers_from_articles(articles)
        logger.warning("  deviz_headers absent din checkpoint — fallback din articole")
    return headers


def main():
    t_start = time.time()

    logger.info("=" * 60)
    logger.info("  Varianta B — Pipeline complet DT2")
    logger.info(f"  Model:   {MODEL}")
    logger.info(f"  Endpoint:{BASE_URL}")
    logger.info(f"  Oferta:  {OFERTA_NR}")
    logger.info("=" * 60)

    client, model = build_client()

    # Step 1: Load articles from DT2 checkpoints
    logger.info("\n--- Extragere articole din checkpoints ---")
    ref_articles, ref_deviz_data = load_articles("di_referinta")
    oferta_articles, oferta_deviz_data = load_articles(f"di_oferta_{OFERTA_NR}")

    logger.info(f"  REF:    {len(ref_articles)} articole valide")
    logger.info(f"  OFERTA: {len(oferta_articles)} articole valide")

    # Step 2: Normalize devize (LLM maps offer deviz codes → ref deviz codes)
    logger.info("\n--- Normalizare devize ---")
    from shared.deviz_normalizer import normalize_devize
    oferta_norm = normalize_devize(ref_articles, oferta_articles, client, model)
    logger.info(f"  Oferta normalizată: {len(oferta_norm)} articole")

    # Step 3: Build DevizHeader objects from checkpoint data
    logger.info("\n--- Construire deviz headers ---")
    ref_headers = build_headers(ref_deviz_data, ref_articles)
    oferta_headers = build_headers(oferta_deviz_data, oferta_norm)
    logger.info(f"  REF:    {len(ref_headers)} grupuri")
    logger.info(f"  OFERTA: {len(oferta_headers)} grupuri")

    # Step 4: Group-based holistic comparison
    logger.info("\n--- Comparare holistica pe grupuri ---")
    from shared.group_comparator import compare_by_groups
    from shared.report_builder import build_raport_holistic

    holistic = compare_by_groups(
        ref_articles,
        oferta_norm,
        ref_headers,
        oferta_headers,
        llm_client=client,
        llm_model=model,
        client_name="DT2-local",
        semantic_cache_path=OUTPUT_DIR / "semantic_cache.json",
    )
    raport = build_raport_holistic(holistic)

    sumar = raport.get("sumar", {})
    elapsed = time.time() - t_start

    logger.info("\n" + "=" * 60)
    logger.info("  REZULTAT FINAL")
    logger.info(f"  Grupuri matched:    {sumar.get('total_matched_groups', 0)}")
    logger.info(f"  Grupuri ref-only:   {sumar.get('total_ref_only_groups', 0)}")
    logger.info(f"  Grupuri oferta-only:{sumar.get('total_oferta_only_groups', 0)}")
    logger.info(f"  Articole matched:   {sumar.get('total_matched_articles', 0)}")
    logger.info(f"  Timp total:         {elapsed:.1f}s")
    logger.info("=" * 60)

    # Step 5: Save output
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_model = MODEL.replace("/", "_").replace(":", "_")
    out_path = OUTPUT_DIR / f"holistic_oferta_{OFERTA_NR}_{safe_model}_{ts}.json"
    out_path.write_text(
        json.dumps(raport, ensure_ascii=False, default=str, indent=2),
        encoding="utf-8",
    )
    logger.info(f"\nOutput: {out_path}")
    logger.info(f"Baseline (claude-sonnet-4-6): output_AO/DT2/holistic_oferta_1.json")


if __name__ == "__main__":
    main()
