"""
Orquestador principal del pipeline ETL para departamentos en CABA.
Orquesta secuencialmente y con PAGINACIÓN ULTRA-MASIVA (hasta 1000 páginas)
la extracción de Zonaprop, Argenprop y Mercado Libre con procesamiento en tiempo real (Stream Processing)
para guardar inmediatamente cada página en MySQL sin saturar la memoria ni perder progreso.
"""

import logging
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from app.db.connection import SessionLocal, init_db, upsert_departamento
from etl.cleaner import clean_departamento_data
from scrapers.zonaprop_scraper import parse_zonaprop_page
from scrapers.argenprop_scraper import parse_argenprop_page
from scrapers.mercadolibre_scraper import parse_mercadolibre_page

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Límite masivo de páginas a recorrer por portal durante la extracción
MAX_PAGES_PER_PORTAL = 2500


BARRIOS_CABA_LIST = [
    "palermo", "belgrano", "recoleta", "caballito", "nunez", "almagro", "villa-crespo",
    "balvanera", "villa-urquiza", "flores", "colegiales", "villa-devoto", "san-telmo",
    "puerto-madero", "barracas", "monserrat", "retiro", "saavedra", "chacarita",
    "coghlan", "floresta", "la-boca", "la-paternal", "liniers", "mataderos",
    "monte-castro", "nueva-pompeya", "parque-avellaneda", "parque-chacabuco",
    "parque-chas", "parque-patricios", "san-cristobal", "san-nicolas", "versalles",
    "villa-del-parque", "villa-general-mitre", "villa-lugano", "villa-luro",
    "villa-ortuzar", "villa-pueyrredon", "villa-real", "villa-santa-rita"
]
AMBIENTES_LIST = [1, 2, 3, 4, 5]

def get_portal_page_url(portal_name: str, page_num: int, barrio_slug: str = None, amb_num: int = None) -> str:
    """
    Genera la URL correspondiente a un número de página según el portal, barrio y cantidad de ambientes.
    """
    if portal_name == "Zonaprop":
        amb_suffix = f"-{amb_num}-ambiente" if amb_num == 1 else f"-{amb_num}-ambientes" if amb_num else ""
        barrio_path = f"-{barrio_slug}" if barrio_slug else "-capital-federal"
        page_suffix = f"-pagina-{page_num}" if page_num > 1 else ""
        return f"https://www.zonaprop.com.ar/departamentos-venta{barrio_path}{amb_suffix}{page_suffix}.html"
    
    elif portal_name == "Argenprop":
        amb_slug = f"-{amb_num}-ambiente" if amb_num == 1 else f"-{amb_num}-ambientes" if amb_num else ""
        base = f"{barrio_slug}{amb_slug}" if barrio_slug else "capital-federal"
        page_suffix = f"-pagina-{page_num}" if page_num > 1 else ""
        return f"https://www.argenprop.com/departamentos/venta/{base}{page_suffix}"
    
    elif portal_name == "Mercado Libre":
        amb_slug = f"{amb_num}-ambiente" if amb_num == 1 else f"{amb_num}-ambientes" if amb_num else None
        if barrio_slug and amb_slug:
            base_path = f"{amb_slug}/capital-federal/{barrio_slug}"
        elif barrio_slug:
            base_path = f"capital-federal/{barrio_slug}"
        else:
            base_path = "capital-federal"
            
        if page_num == 1:
            return f"https://inmuebles.mercadolibre.com.ar/departamentos/venta/{base_path}/"
        offset = ((page_num - 1) * 48) + 1
        return f"https://inmuebles.mercadolibre.com.ar/departamentos/venta/{base_path}/_Desde_{offset}_NoIndex_True"
    
    return ""


PORTAL_TARGETS = [
    {"name": "Mercado Libre", "parser": parse_mercadolibre_page},
    {"name": "Zonaprop", "parser": parse_zonaprop_page},
    {"name": "Argenprop", "parser": parse_argenprop_page},
]


import random
import time

def handle_cookie_banners(page, portal_name: str):
    """
    Intenta detectar y cerrar/aceptar banners de consentimiento de cookies o modales emergentes
    con un timeout corto (3s) envuelto en try/except para no interrumpir la extracción.
    """
    banner_selectors = [
        "button:has-text('Aceptar')",
        "button:has-text('Entendido')",
        "button:has-text('Accept')",
        "button:has-text('De acuerdo')",
        "#didomi-notice-agree-button",
        ".cookie-banner-close",
        "[aria-label='Cerrar']",
        "[aria-label='Close']"
    ]
    for selector in banner_selectors:
        try:
            btn = page.query_selector(selector)
            if btn and btn.is_visible():
                btn.click(timeout=3000)
                logger.info(f"[{portal_name}] Cookie/Modal banner cerrado exitosamente ({selector}).")
                break
        except Exception:
            pass


from urllib.request import Request, urlopen
import cloudscraper

_cloudscraper_instance = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_portal_html(page, url: str, portal_name: str) -> str:
    """
    Obtiene el contenido HTML navegando con motor HTTP ultra-rápido (urllib/cloudscraper) o Playwright con evasión WAF.
    """
    # 1. Para Zonaprop u otros portales, intentar extracción urllib/cloudscraper ultra-rápida (25 avisos/pag sin JS)
    try:
        req = Request(url, headers=_HTTP_HEADERS)
        with urlopen(req, timeout=12) as response:
            html = response.read().decode('utf-8')
            if "postingCard" in html or "listing__item" in html or "card-container" in html:
                return html
    except Exception:
        pass

    try:
        res = _cloudscraper_instance.get(url, timeout=12)
        if res.status_code == 200 and "Human Verification" not in res.text and ("postingCard" in res.text or "listing__item" in res.text):
            return res.text
    except Exception:
        pass

    # 2. Fallback a Playwright con evasión avanzada
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1000)
        
        # Detección de Challenge AWS WAF y auto-recuperación con token de sesión
        title = page.title()
        if any(w in title for w in ["Human Verification", "Just a moment", "AWS WAF", "Challenge"]):
            logger.warning(f"[{portal_name}] Reto WAF detectado ('{title}'). Esperando resolución JS y recargando...")
            page.wait_for_timeout(4000)
            page.reload(wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1000)
            title = page.title()
            logger.info(f"[{portal_name}] Título tras auto-reload WAF: '{title}' | URL: {page.url}")
        
        # Cerrar banners emergentes / de cookies antes de extraer
        handle_cookie_banners(page, portal_name)
        
        return page.content()
    except Exception as e:
        logger.error(f"[{portal_name}] Error al extraer HTML de {url}: {e}")
        return ""


def run_pipeline(targets: List[Dict[str, Any]] = None, max_pages: int = MAX_PAGES_PER_PORTAL):
    """
    Ejecuta el ciclo de vida completo de ETL multi-portal con paginación masiva de hasta 1000 páginas:
    - Procesamiento Stream (Página a Página): Cada página raspada se limpia e inserta/actualiza INMEDIATAMENTE en MySQL.
    - Robusto ante desconexiones o fallos: Los datos se persisten al instante.
    """
    if targets is None:
        targets = PORTAL_TARGETS

    # Inicializar las tablas de la base de datos en MySQL
    init_db()

    total_guardados = 0
    total_errores = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                locale="es-AR",
                timezone_id="America/Argentina/Buenos_Aires"
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            for target in targets:
                portal_name = target["name"]
                parser_fn = target["parser"]
                portal_guardados = 0
                
                logger.info(f"=== INICIANDO EXTRACCIÓN MASIVA HASTA {max_pages} PÁGINAS PARA: {portal_name.upper()} ===")
                sub_slugs = BARRIOS_CABA_LIST

                for b_slug in BARRIOS_CABA_LIST:
                    if portal_name == "Zonaprop":
                        amb_iterations = [None]
                    else:
                        amb_iterations = [None] + AMBIENTES_LIST

                    for amb_num in amb_iterations:
                        amb_label = f" - {amb_num} amb" if amb_num else ""
                        label_suffix = f" ({b_slug}{amb_label})"
                        consecutive_empty = 0

                        for page_num in range(1, max_pages + 1):
                            url = get_portal_page_url(portal_name, page_num, b_slug, amb_num)
                            html_content = fetch_portal_html(page, url, f"{portal_name}{label_suffix} Pág {page_num}")
                        
                            if not html_content:
                                consecutive_empty += 1
                                title_raw = page.title()
                                logger.warning(f"[{portal_name}{label_suffix}] HTML Vacío en pág {page_num}. Título detectado: '{title_raw}'")
                                if consecutive_empty >= 2:
                                    logger.info(f"[{portal_name}{label_suffix}] Fin de páginas disponible (sin HTML). Avanzando.")
                                    break
                                continue

                            try:
                                raw_items = parser_fn(html_content)
                                count = len(raw_items)
                                
                                if count == 0:
                                    consecutive_empty += 1
                                    title_raw = page.title()
                                    logger.warning(f"[{portal_name}{label_suffix}] 0 departamentos en pág {page_num}. Título detectado: '{title_raw}' | URL: {page.url}")
                                    if consecutive_empty >= 2:
                                        logger.info(f"[{portal_name}{label_suffix}] Fin de publicaciones disponibles. Avanzando.")
                                        break
                                    continue

                                consecutive_empty = 0

                                # PERSISTENCIA INMEDIATA PÁGINA A PÁGINA (STREAM ETL EN MYSQL)
                                db_session = SessionLocal()
                                page_success = 0
                                for raw_item in raw_items:
                                    try:
                                        cleaned_item = clean_departamento_data(raw_item)
                                        upsert_departamento(db_session, cleaned_item)
                                        page_success += 1
                                    except Exception as e:
                                        total_errores += 1
                                        continue
                                
                                db_session.close()

                                portal_guardados += page_success
                                total_guardados += page_success

                                logger.info(f"[{portal_name}{label_suffix}] Pág {page_num}/{max_pages}: {page_success}/{count} avisos guardados en MySQL. (Total acumulado: {portal_guardados})")

                            except Exception as e:
                                logger.error(f"[{portal_name}{label_suffix}] Error parseando pág {page_num}: {e}")

                            # Retardo aleatorio de seguridad (2 a 5 segundos) entre páginas para evasión anti-bot
                            sleep_time = round(random.uniform(2.0, 5.0), 2)
                            time.sleep(sleep_time)

                logger.info(f"=== COMPLETADO {portal_name.upper()}: {portal_guardados} publicaciones guardadas en la BD ===")

            browser.close()

        # Ejecutar depuración automática post-ETL de publicaciones falsas o inválidas
        from etl.clean_fake_listings import audit_and_purge_fake_listings
        audit_res = audit_and_purge_fake_listings(commit=True)

        logger.info(f"=== ETL MASIVO Y DEPURACIÓN COMPLETADOS CON ÉXITO: {total_guardados} publicaciones procesadas | Purgados post-ETL: {audit_res['total_purgados']} | Total Válidos en MySQL: {audit_res['total_restantes']:,} ===")

    except Exception as e:
        logger.error(f"Error crítico durante la ejecución del pipeline orquestador: {e}")


if __name__ == "__main__":
    run_pipeline()
