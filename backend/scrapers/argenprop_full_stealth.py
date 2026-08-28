"""
Extractor Masivo de Argenprop con Playwright Stealth y Navegación Persistente.
Supera la protección Cloudflare WAF de Argenprop utilizando cookies persistentes y la sintaxis de URL oficial `-pagina-N`.
"""

import os
import sys
import time
import logging
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.connection import SessionLocal, init_db, upsert_departamento
from etl.cleaner import clean_departamento_data
from scrapers.argenprop_scraper import parse_argenprop_page
from etl.clean_fake_listings import audit_and_purge_fake_listings
from main_etl import BARRIOS_CABA_LIST, AMBIENTES_LIST

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_full_argenprop_stealth(max_pages_per_search: int = 50):
    init_db()
    logger.info("=== INICIANDO EXTRACCIÓN MASIVA COMPLETA DE ARGENPROP (PLAYWRIGHT STEALTH) ===")

    with sync_playwright() as p:
        # Usar modo gráfico con argumentos anti-bot para paso garantizado de WAF
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="es-AR"
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        logger.info("Paso 1: Inicializando cookies WAF en la portada de Argenprop...")
        page.goto("https://www.argenprop.com/", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        if "Human Verification" in page.title() or "Just a moment" in page.title():
            logger.info("Esperando resolución automática de Cloudflare WAF...")
            page.wait_for_timeout(5000)

        logger.info(f"Sesión WAF activa. Portada cargada con éxito: '{page.title()}'")

        total_guardados = 0
        session = SessionLocal()

        for barrio_slug in BARRIOS_CABA_LIST:
            for amb_num in [None] + AMBIENTES_LIST:
                amb_slug = f"-{amb_num}-ambiente" if amb_num == 1 else f"-{amb_num}-ambientes" if amb_num else ""
                base_url = f"https://www.argenprop.com/departamentos/venta/{barrio_slug}{amb_slug}"

                barrio_guardados = 0
                for p_num in range(1, max_pages_per_search + 1):
                    url = base_url if p_num == 1 else f"{base_url}-pagina-{p_num}"

                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=25000)
                        page.wait_for_timeout(1000)

                        if "Human Verification" in page.title():
                            page.wait_for_timeout(4000)

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

                        total_guardados += pg_saved
                        barrio_guardados += pg_saved

                    except Exception as e:
                        logger.warning(f"Error procesando {url}: {e}")
                        break

                if barrio_guardados > 0:
                    logger.info(f"[ARGENPROP ({barrio_slug} - {amb_num or 'todos'} amb)] {barrio_guardados} avisos guardados. (Total acumulado en MySQL: {total_guardados})")

        session.close()
        browser.close()

    logger.info(f"=== EXTRACCIÓN COMPLETADA DE ARGENPROP: {total_guardados} publicaciones guardadas ===")
    
    # Depuración de publicaciones falsas post-ETL
    audit_res = audit_and_purge_fake_listings(commit=True)
    logger.info(f"=== DEPURACIÓN APLICADA: Total Válidos en MySQL: {audit_res['total_restantes']:,} ===")


if __name__ == "__main__":
    run_full_argenprop_stealth(max_pages_per_search=30)
