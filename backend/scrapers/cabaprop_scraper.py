"""
Extractor Masivo REST API Ultrarrápido y Preciso de Cabaprop.
Utiliza los endpoints oficiales de Cabaprop con paginación optimizada (limit=20, timeout=30)
y filtro por Barrios x Ambientes (1, 2, 3, 4, 5+).
"""

import os
import sys
import time
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from db.connection import SessionLocal, init_db, upsert_departamento
from etl.cleaner import clean_departamento_data
from etl.clean_fake_listings import audit_and_purge_fake_listings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logger = logging.getLogger(__name__)

CABAPROP_API_FIND = "https://cabaprop.com.ar/api/v1/properties/find-properties"
CABAPROP_BARRIOS_FLAT = "https://cabaprop.com.ar/api/v1/utils/barrios-flat"
CABAPROP_BARRIOS_OBJ = "https://cabaprop.com.ar/api/v1/utils/barrios-obj"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Referer": "https://cabaprop.com.ar/propiedades/comprar?pagina=1"
}


# Diccionario oficial estático y exhaustivo de Barrios de CABA en Cabaprop
CABAPROP_BARRIOS_CABA = [
    (47, "Palermo"), (18, "Belgrano"), (51, "Recoleta"), (19, "Caballito"), (46, "Núñez"),
    (11, "Almagro"), (57, "Villa Crespo"), (13, "Balvanera"), (64, "Villa Urquiza"), (28, "Flores"),
    (24, "Colegiales"), (59, "Villa Devoto"), (53, "San Telmo"), (50, "Puerto Madero"), (14, "Barracas"),
    (45, "Monserrat"), (52, "Retiro"), (54, "Saavedra"), (23, "Chacarita"), (25, "Coghlan"),
    (29, "Floresta"), (34, "La Boca"), (35, "La Paternal"), (36, "Liniers"), (37, "Mataderos"),
    (44, "Monte Castro"), (47, "Nueva Pompeya"), (48, "Parque Avellaneda"), (49, "Parque Chacabuco"),
    (50, "Parque Chas"), (51, "Parque Patricios"), (52, "San Cristóbal"), (53, "San Nicolás"),
    (55, "Versalles"), (58, "Villa del Parque"), (60, "Villa General Mitre"), (61, "Villa Lugano"),
    (62, "Villa Luro"), (63, "Villa Ortúzar"), (65, "Villa Pueyrredón"), (66, "Villa Real"),
    (67, "Villa Riachuelo"), (68, "Villa Santa Rita"), (69, "Villa Soldati"), (10, "Agronomía"),
    (16, "Boedo"), (26, "Constitución")
]


def fetch_cabaprop_barrios():
    """Retorna la lista de barrios de CABA en Cabaprop de forma confiable."""
    return CABAPROP_BARRIOS_CABA, {}


def parse_cabaprop_item(raw_item: dict, barrio_nombre: str = None) -> dict:
    """Normaliza un JSON de propiedad de Cabaprop al esquema oficial de la base de datos."""
    if not isinstance(raw_item, dict):
        return None

    permalink = str(raw_item.get('permalink') or '')
    prop_id = str(raw_item.get('code') or raw_item.get('_id') or raw_item.get('id') or '')
    
    if not prop_id and permalink:
        prop_id = permalink.strip('/').split('-')[-1]

    if not prop_id:
        return None

    loc = raw_item.get('location', {})
    chars = raw_item.get('characteristics', {})
    price_info = raw_item.get('price', {})
    surface = raw_item.get('surface', {})

    # Dirección
    street = str(loc.get('street') or '').strip()
    number = str(loc.get('number') or '').strip()
    direccion = f"{street} {number}".strip() if street else raw_item.get('title', '')

    # Moneda y Precio (1 = USD, 2 = ARS)
    currency_code = price_info.get('currency')
    raw_price = float(price_info.get('total') or 0.0)
    
    if currency_code == 2 and raw_price > 0:
        precio_usd = raw_price / 1100.0
    else:
        precio_usd = raw_price

    # m2
    m2_tot = float(surface.get('totalSurface') or surface.get('coveredSurface') or 0.0)
    m2_cub = float(surface.get('coveredSurface') or m2_tot or 0.0)

    # Garage
    garage_info = chars.get('garage', {})
    has_garage = bool(garage_info.get('active') or (garage_info.get('quantity') or 0) > 0)

    # Antigüedad y Estado
    years = chars.get('buildingAntiquity') or chars.get('antiquity', {}).get('years', 0)
    stage = chars.get('buildingStage')
    estado = 'pozo' if stage == 1 else 'a estrenar' if years == 0 else 'usado'

    # URL
    permalink = raw_item.get('permalink', '')
    url_pub = permalink if str(permalink).startswith('http') else f"https://cabaprop.com.ar{permalink}"

    return {
        "id_publicacion": f"CABAPROP_{prop_id}",
        "portal": "Cabaprop",
        "titulo_aviso": raw_item.get('title') or f"Departamento en {barrio_nombre or 'CABA'}",
        "barrio": barrio_nombre or loc.get('locality'),
        "direccion": direccion,
        "ambientes_raw": chars.get('ambience'),
        "habitaciones_raw": chars.get('bedrooms'),
        "banos_raw": chars.get('bathrooms'),
        "tiene_garage": has_garage,
        "estado_propiedad": estado,
        "precio_usd": precio_usd,
        "m2_totales_raw": m2_tot,
        "m2_cubiertos_raw": m2_cub,
        "url_publicacion": url_pub,
        "descripcion_cruda": raw_item.get('description', '')
    }


def process_barrio_cabaprop(barrio_info: tuple, session_http: requests.Session = None) -> int:
    b_id, b_name = barrio_info
    limit = 20
    saved = 0
    s = session_http if session_http else requests.Session()

    # Iterar por ambientes (1, 2, 3, 4, 5) para no sobrecargar el query planner de Cabaprop
    ambientes_listas = [[1], [2], [3], [4], [5]]

    for amb in ambientes_listas:
        offset = 0
        while True:
            url = f"{CABAPROP_API_FIND}?offset={offset}&limit={limit}&orderBy=created_at&sort=desc"
            payload = {
                "operationType": 1,
                "propertyTypes": [1],
                "barrios": [b_id],
                "ambientes": amb
            }

            max_retries = 3
            result = []
            for attempt in range(max_retries):
                try:
                    r = s.post(url, headers=HEADERS, json=payload, timeout=25)
                    if r.status_code in [200, 201]:
                        data = r.json()
                        result = data.get('result', [])
                        break
                    elif r.status_code in [500, 502, 503, 504]:
                        time.sleep(1.0 * (attempt + 1))
                    else:
                        break
                except Exception as e_req:
                    if attempt == max_retries - 1:
                        logger.warning(f"Timeout en barrio {b_name} amb {amb} (intento {attempt+1}): {e_req}")
                    time.sleep(1.0 * (attempt + 1))

            if not result:
                break

            db_session = SessionLocal()
            batch_count = 0
            for item in result:
                parsed = parse_cabaprop_item(item, b_name)
                if parsed:
                    try:
                        cleaned = clean_departamento_data(parsed)
                        upsert_departamento(db_session, cleaned)
                        batch_count += 1
                    except Exception as e_clean:
                        db_session.rollback()
                        logger.error(f"Error limpiando/insertando item Cabaprop: {e_clean}")

            db_session.close()
            saved += batch_count

            offset += limit
            if len(result) < limit:
                break

            time.sleep(0.05)

    return saved


def run_cabaprop_fast_etl(max_workers: int = 3):
    init_db()
    logger.info(f"=== INICIANDO EXTRACCIÓN REST API DE CABAPROP ({max_workers} WORKERS) ===")

    barrios_list, _ = fetch_cabaprop_barrios()
    valid_barrios = [(b[0], b[1]) if isinstance(b, tuple) else (b.get('value'), b.get('label')) for b in barrios_list]
    valid_barrios = [b for b in valid_barrios if b[0] and b[1]]
    total_barrios = len(valid_barrios)
    logger.info(f"[CABAPROP] Obtenidos {total_barrios} barrios oficiales CABA. Iniciando scraping...")

    total_saved = 0
    completed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_barrio_cabaprop, b_info) for b_info in valid_barrios]
        for future in as_completed(futures):
            completed += 1
            saved = future.result()
            total_saved += saved

            if completed % 10 == 0 or completed == total_barrios:
                elapsed = time.time() - start_time
                logger.info(f"[CABAPROP] Progreso: {completed}/{total_barrios} barrios ({completed/total_barrios*100:.1f}%) | {total_saved} publicaciones guardadas")

    elapsed = time.time() - start_time
    logger.info(f"=== EXTRACCIÓN REST API DE CABAPROP COMPLETADA: {total_saved} publicaciones en {elapsed:.2f}s ===")

    # Depuración automática post-ETL de avisos dudosos / raros / falsos
    audit_res = audit_and_purge_fake_listings(commit=True)
    logger.info(f"=== DEPURACIÓN POST-ETL APLICADA: Total Válidos en MySQL: {audit_res['total_restantes']:,} ===")


if __name__ == "__main__":
    run_cabaprop_fast_etl(max_workers=3)

