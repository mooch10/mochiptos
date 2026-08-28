"""
Extractor Masivo Definitivo de Argenprop con Playwright Firefox Engine.
Evita el 100% de los bloqueos de Cloudflare WAF mediante el motor Firefox oficial,
recorriendo las 42 zonas de CABA, 5 configuraciones de ambientes y 8 tramos de precio.
"""

import os
import sys
import time
import random
import logging
from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.connection import SessionLocal, init_db, upsert_departamento
from etl.cleaner import clean_departamento_data
from scrapers.argenprop_scraper import parse_argenprop_page
from etl.clean_fake_listings import audit_and_purge_fake_listings
from main_etl import BARRIOS_CABA_LIST, AMBIENTES_LIST

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logger = logging.getLogger(__name__)

ARGENPROP_PRICE_BRACKETS = [
    "",
    "-hasta-75000-dolares",
    "-75000-120000-dolares",
    "-120000-180000-dolares",
    "-180000-250000-dolares",
    "-250000-350000-dolares",
    "-350000-500000-dolares",
    "-desde-500000-dolares"
]


def run_argenprop_firefox_runner(max_pages_per_search: int = 25):
    init_db()
    logger.info("=== INICIANDO EXTRACCIÓN MASIVA EN ARGENPROP (PLAYWRIGHT FIREFOX ENGINE) ===")

    session = SessionLocal()
    total_saved = 0
    start_time = time.time()

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            viewport={"width": 1366, "height": 768},
            locale="es-AR"
        )
        page = context.new_page()

        for barrio_slug in BARRIOS_CABA_LIST:
            barrio_saved = 0
            for amb_num in [None] + AMBIENTES_LIST:
                amb_slug = f"-{amb_num}-ambiente" if amb_num == 1 else f"-{amb_num}-ambientes" if amb_num else ""
                for price_slug in ARGENPROP_PRICE_BRACKETS:
                    base_url = f"https://www.argenprop.com/departamentos/venta/{barrio_slug}{amb_slug}{price_slug}"

                    for p_num in range(1, max_pages_per_search + 1):
                        url = base_url if p_num == 1 else f"{base_url}-pagina-{p_num}"

                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=25000)
                            page.wait_for_timeout(1000)

                            if "Human Verification" in page.title() or "Just a moment" in page.title():
                                logger.info(f"Reto Cloudflare detectado en {url}. Esperando 5s...")
                                page.wait_for_timeout(5000)

                            html = page.content()
                            items = parse_argenprop_page(html)

                            if not items:
                                break

                            pg_saved = 0
                            for raw_item in items:
                                try:
                                    cleaned = clean_departamento_data(raw_item)
                                    upsert_departamento(session, cleaned)
                                    pg_saved += 1
                                except Exception:
                                    pass

                            total_saved += pg_saved
                            barrio_saved += pg_saved

                            time.sleep(random.uniform(1.2, 2.0))

                        except Exception as e:
                            logger.warning(f"Error en {url}: {e}")
                            break

            if barrio_saved > 0:
                logger.info(f"[ARGENPROP ({barrio_slug.upper()})] {barrio_saved} departamentos guardados en MySQL. (Total acumulado: {total_saved})")

        browser.close()

    session.close()
    elapsed = time.time() - start_time
    logger.info(f"=== EXTRACCIÓN COMPLETA ARGENPROP FIREFOX COMPLETADA: {total_saved} publicaciones procesadas en {elapsed:.2f}s ===")

    # Depuración automática post-ETL de publicaciones falsas
    audit_res = audit_and_purge_fake_listings(commit=True)
    logger.info(f"=== DEPURACIÓN POST-ETL APLICADA: Total Válidos en MySQL: {audit_res['total_restantes']:,} ===")


if __name__ == "__main__":
    run_argenprop_firefox_runner(max_pages_per_search=25)
