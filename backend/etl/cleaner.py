import re
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
except Exception:
    import pytz
    LOCAL_TZ = pytz.timezone("America/Argentina/Buenos_Aires")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DOLAR_API_URL = "https://dolarapi.com/v1/dolares/blue"


def get_dolar_blue_rate() -> float:
    """
    Obtiene la cotización de venta del Dólar Blue desde DolarAPI.
    """
    try:
        response = requests.get(DOLAR_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        rate = float(data.get("venta", 0))
        if rate <= 0:
            raise ValueError(f"Valor de cotización inválido devuelto por API: {rate}")
        return rate
    except Exception as e:
        logger.error(f"Error al obtener el tipo de cambio desde DolarAPI: {e}")
        raise


def extract_number(val: Optional[str], is_float: bool = False) -> Optional[Any]:
    """
    Extrae números de una cadena usando expresiones regulares.
    Si la cadena contiene formato español (ej: "$ 490.000 Expensas", "50,5" o "2.400.000"), formatea adecuadamente.
    """
    if not val:
        return None
    
    val_str = str(val).strip()
    # Buscar el primer bloque numérico que puede contener dígitos, puntos y comas
    num_match = re.search(r"(\d+(?:[\.,]\d+)*)", val_str)
    if not num_match:
        return None
        
    candidate = num_match.group(1)
    
    # 1. Caso estándar de miles con puntos: "490.000" o "2.400.000"
    if "." in candidate and "," not in candidate:
        parts = candidate.split(".")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            candidate = "".join(parts)
        elif len(parts) == 2 and len(parts[1]) == 3:
            candidate = candidate.replace(".", "")

    # 2. Caso con comas y puntos: "120.000,50" -> "120000.50"
    elif "." in candidate and "," in candidate:
        candidate = candidate.replace(".", "").replace(",", ".")
    
    # 3. Caso sólo con comas decimales: "50,5" -> "50.5"
    elif "," in candidate and "." not in candidate:
        candidate = candidate.replace(",", ".")
            
    try:
        return float(candidate) if is_float else int(float(candidate))
    except ValueError:
        return None


def extract_desarrolladora(texto: str, estado_propiedad: str) -> Optional[str]:
    """
    Extrae el nombre de la empresa desarrolladora, constructora o estudio de arquitectura.
    """
    if not texto:
        return None

    # Lista extendida de desarrolladoras y constructoras reconocidas en Argentina
    CONOCIDAS = [
        "Toribio Achaval", "Baigun", "TGLT", "Raghsa", "Consultatio", "Argencons", 
        "Portland", "Brody Bornstein", "Spazios", "Lepore", "D'Aria", "Korn", "Ginevra",
        "Interwin", "Monier", "MRA+A", "Mario Roberto Alvarez", "Dujovne Hirsch",
        "Brody", "Northbaires", "ABV", "Quba", "Gerlach Campbell", "BMA", "Aisenson",
        "MSGSSS", "D'Odorico", "Creaurban", "CRIBA", "Quartier", "Le Parc", "Chateau",
        "Alvear Tower", "Link", "Astilleros", "RE/MAX", "Ocampo", "Loria", "Pellegrini",
        "SLS Properties", "Veneto", "Aston", "BMA Arquitectos", "Dujovne", "G7", "Tavella"
    ]
    for brand in CONOCIDAS:
        if re.search(r"\b" + re.escape(brand) + r"\b", texto, re.IGNORECASE):
            return brand

    # Patrones específicos con prefijos explícitos de desarrollo
    patrones = [
        r"(?:desarrolla|desarrollador|desarrolladora|construye|constructora|estudio|arquitectura|arquitectos?|emprendimiento|proyecto)\s*[:\-]\s*([A-ZÁÉÍÓÚÑ][A-Za-z0-9ÁÉÍÓÚÑáéíóúñ\.\s&]{2,30})",
        r"(?:proyecto de|obra de|estudio de arquitectura)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ][A-Za-z0-9ÁÉÍÓÚÑáéíóúñ\.\s&]{2,30})",
        r"(?:Edificio|Torre)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})"
    ]
    
    stop_words = [
        "EXCELENTE", "CALIDAD", "CATEGORIA", "DEPARTAMENTO", "VENTA", "ALQUILER", 
        "ZONA", "BUENOS AIRES", "CAPITAL", "PALERMO", "BELGRANO", "QUE COMBINA", "TIENE UNA",
        "EN PALERMO", "EN CONSTRUCCION", "ESTRENAR", "POZO", "EMPRENDIMIENTO", "CUCICBA",
        "CUENTA CON", "SEGURIDAD", "TIENE", "YA", "DE CATEGORIA", "CON BALCON", "EN VENTA"
    ]

    for pat in patrones:
        m = re.search(pat, texto)
        if m:
            cand = m.group(1).strip()
            cand_upper = cand.upper()
            if not any(stop in cand_upper for stop in stop_words) and len(cand) >= 4:
                if not any(v in cand.lower().split() for v in ["tiene", "cuenta", "posee", "con", "ya", "una", "un"]):
                    return cand[:100]

    return None


def clean_departamento_data(raw_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma y limpia el diccionario de datos crudos extraídos por los scrapers,
    generando los campos derivados y adaptándolo estrictamente al esquema de la base de datos `departamentos`.
    """
    try:
        now = datetime.now(LOCAL_TZ)

        # 1. Limpieza de números básicos (ambientes, habitaciones, baños, m2_totales, m2_cubiertos)
        ambientes = extract_number(raw_dict.get("ambientes_raw"), is_float=False)
        habitaciones = extract_number(raw_dict.get("habitaciones_raw"), is_float=False)
        banos = extract_number(raw_dict.get("banos_raw"), is_float=False)
        m2_totales = extract_number(raw_dict.get("m2_totales_raw"), is_float=True)
        m2_cubiertos = extract_number(raw_dict.get("m2_cubiertos_raw"), is_float=True)

        # Inferencia y corrección prioritaria de ambientes (Monoambiente prevalece)
        raw_titulo_lower = str(raw_dict.get("titulo_aviso") or "").lower()
        raw_url_lower = str(raw_dict.get("url_publicacion") or "").lower()
        desc_raw_lower = str(raw_dict.get("descripcion_cruda") or "").lower()
        full_text_amb = f"{raw_titulo_lower} {raw_url_lower} {desc_raw_lower}"

        is_monoambiente = any(kw in full_text_amb for kw in ["monoambiente", "monambiente", "1-ambiente", "1-ambientes", "1 amb", "1amb", "studio", "estudio"])
        if is_monoambiente:
            ambientes = 1
        elif ambientes is None:
            if any(kw in full_text_amb for kw in ["2-ambiente", "2-ambientes", "2 amb", "2amb", "dos amb"]):
                ambientes = 2
            elif any(kw in full_text_amb for kw in ["3-ambiente", "3-ambientes", "3 amb", "3amb", "tres amb"]):
                ambientes = 3
            elif any(kw in full_text_amb for kw in ["4-ambiente", "4-ambientes", "4 amb", "4amb", "cuatro amb"]):
                ambientes = 4
            else:
                ambientes = 1

        # Inferencia de m2_totales si m2_totales es None o < 20.0
        if m2_totales is None or m2_totales < 20.0:
            if ambientes == 1:
                m2_totales = 30.0
            elif ambientes == 2:
                m2_totales = 48.0
            elif ambientes == 3:
                m2_totales = 68.0
            elif ambientes == 4:
                m2_totales = 95.0
            elif ambientes == 5:
                m2_totales = 140.0
            else:
                m2_totales = 45.0

        # m2_cubiertos: Aislar estrictamente de los totales (m2_cubiertos <= m2_totales)
        if m2_cubiertos is not None:
            if m2_cubiertos > m2_totales or m2_cubiertos < 15.0:
                m2_cubiertos = round(m2_totales * 0.90, 1)
        else:
            m2_cubiertos = round(m2_totales * 0.90, 1)

        # Regla de Negocio: Todo departamento en venta cuenta con al menos 1 baño por defecto
        if banos is None:
            banos = 1

        # 2. Precio y Moneda (Conversión si aplica)
        precio_raw = str(raw_dict.get("precio_raw") or "")
        precio_num = extract_number(precio_raw, is_float=True)
        
        precio_usd: Optional[float] = None
        if raw_dict.get("precio_usd") is not None and float(raw_dict.get("precio_usd")) > 0:
            precio_usd = round(float(raw_dict.get("precio_usd")), 2)
        elif precio_num is not None:
            upper_precio = precio_raw.upper()
            is_usd = any(curr in upper_precio for curr in ["USD", "U$S", "US$"])
            if "ARS" in upper_precio or ("$" in upper_precio and not is_usd):
                tc = get_dolar_blue_rate()
                precio_usd = round(precio_num / tc, 2)
                logger.info(f"Precio en ARS ({precio_num}) convertido a USD ({precio_usd}) usando TC {tc}")
            else:
                precio_usd = round(precio_num, 2)

        if precio_usd is None or precio_usd <= 0:
            precio_usd = round((m2_totales or 45.0) * 1800.0, 2)

        # 3. Precio por m2 y control de anomalía superior a 35.000 USD/m2
        precio_m2: Optional[float] = None
        if precio_usd and m2_totales and m2_totales > 0:
            precio_m2 = round(precio_usd / m2_totales, 2)
            if precio_m2 > 35000.0:
                est_m2 = 30.0 if ambientes == 1 else 48.0 if ambientes == 2 else 68.0 if ambientes == 3 else 95.0 if ambientes == 4 else 140.0
                m2_totales = est_m2
                precio_m2 = round(precio_usd / m2_totales, 2)
                if precio_m2 > 35000.0:
                    precio_m2 = 35000.0

        # 5. Descripción Cruda íntegra
        descripcion_cruda = str(raw_dict.get("descripcion_cruda") or raw_dict.get("titulo_aviso") or "").strip()
        desc_lower = descripcion_cruda.lower()
        full_text_lower = f"{raw_titulo_lower} {desc_lower}"

        # 4. Expensas (Valor numérico limpio. Si no hay, buscar en texto crudo)
        expensas_raw = raw_dict.get("expensas_raw")
        expensas = 0.0
        if expensas_raw:
            exp_num = extract_number(expensas_raw, is_float=True)
            if exp_num is not None and exp_num > 0:
                expensas = float(exp_num)

        if expensas == 0.0:
            exp_m = re.search(r"(?:expensas|exp\.?|gastos\s+comunes)\s*(?:[:\$-]|\bde\b)?\s*\$?\s*([\d\.\,]{3,10})", full_text_lower)
            if not exp_m:
                exp_m = re.search(r"\$?\s*([\d\.\,]{3,10})\s*(?:de\s*)?(?:expensas|exp\.?)", full_text_lower)
            if exp_m:
                cand = exp_m.group(1).replace(".", "").replace(",", ".")
                try:
                    val = float(cand)
                    if 1000.0 <= val <= 3000000.0:
                        expensas = val
                except ValueError:
                    pass

        # 6. Antigüedad (Priorizar años explícitos > 0, luego pozo/estrenar -> 0)
        antiguedad_raw = str(raw_dict.get("antiguedad_raw") or "").lower()
        combined_ant_text = f"{antiguedad_raw} {full_text_lower}"
        antiguedad = 0

        # 6.1 Años numéricos explícitos
        ant_match = re.search(r"(\d+)\s*(?:años?|anos?)\s*(?:de\s*)?(?:antigüedad|antiguedad|antiguo)?", combined_ant_text)
        if not ant_match:
            ant_match = re.search(r"(?:antigüedad|antiguedad|antig\.?)\s*[:\-]?\s*(\d+)", combined_ant_text)
        if not ant_match:
            ant_match = re.search(r"edificio\s*(?:de\s*)?(\d+)\s*(?:años?|anos?)", combined_ant_text)

        if ant_match:
            try:
                val = int(ant_match.group(1))
                if 1 <= val <= 120:
                    antiguedad = val
            except ValueError:
                antiguedad = 0

        # 6.2 Si no se halló antigüedad > 0 y el aviso habla de pozo/estrenar -> 0
        if antiguedad == 0:
            if any(kw in combined_ant_text for kw in ["a estrenar", "estrenar", "en pozo", "pozo", "en construccion", "emprendimiento", "obra"]):
                antiguedad = 0

        # 7. Disposición (Texto: Frente, Contrafrente, Lateral, Interno)
        disposicion = None
        disposicion_raw = str(raw_dict.get("disposicion_raw") or "").lower()
        full_disp_text = f"{disposicion_raw} {full_text_lower}"

        if re.search(r"\b(?:al\s+)?contrafrente\b|\bcontra\-?frente\b|\bc\/frente\b|\bc\-frente\b|\bpulmon\s+de\s+manzana\b", full_disp_text):
            disposicion = "Contrafrente"
        elif re.search(r"\b(?:al\s+)?frente\b|\bal\s+frte\b|\bal\s+fte\b|\bfrente\s+a\b|\bvista\s+al\s+frente\b", full_disp_text):
            disposicion = "Frente"
        elif re.search(r"\blateral\b|\bal\s+lateral\b", full_disp_text):
            disposicion = "Lateral"
        elif re.search(r"\binterno\b|\binterior\b|\bal\s+interno\b|\bpatio\s+interno\b", full_disp_text):
            disposicion = "Interno"

        # 8. Ingeniería de Características (Fase 2)
        # tiene_cochera (Booleano)
        tiene_cochera = False
        cochera_keywords = ["cochera", "cocheras", "garage", "garaje", "guarda coche", "guardacoches", "guardacoche", "estacionamiento", "coch.", "coch", "vehiculo", "auto"]
        negaciones_cochera = ["sin cochera", "no tiene cochera", "no posee cochera", "sin garage", "sin garaje", "no incluye cochera", "cochera opcional", "posibilidad de cochera", "opcion a cochera", "consul. cochera"]
        
        has_pos_cochera = any(re.search(r"\b" + re.escape(kw) + r"\b", full_text_lower) for kw in cochera_keywords)
        has_neg_cochera = any(neg in full_text_lower for neg in negaciones_cochera)
        
        if has_pos_cochera and not has_neg_cochera:
            tiene_cochera = True

        # tiene_amenities (Booleano)
        amenities_keywords = [
            "amenities", "amenitie", "sum", "pileta", "piscina", "gimnasio", "gym", 
            "laundry", "parrilla", "solarium", "solárium", "jacuzzi", "sauna", "quincho", 
            "seguridad 24", "vigilancia", "totem", "losa radiante", "balcón", "balcon", 
            "terraza", "playroom", "cancha", "coworking"
        ]
        tiene_amenities = any(re.search(r"\b" + re.escape(akw) + r"\b", full_text_lower) for akw in amenities_keywords)

        # desarrolladora (Texto)
        estado_propiedad_cand = "En construcción" if any(kw in full_text_lower for kw in ["pozo", "en construccion", "construcción", "emprendimiento", "obra"]) else ("A estrenar" if any(kw in full_text_lower for kw in ["a estrenar", "estrenar"]) else "Estrenado")
        desarrolladora = extract_desarrolladora(f"{raw_dict.get('titulo_aviso', '')} {descripcion_cruda}", estado_propiedad_cand)

        # 9. Mapeo exhaustivo de barrios oficiales de CABA
        MAPEO_BARRIOS = {
            "Las Cañitas": "Palermo",
            "Palermo Hollywood": "Palermo",
            "Palermo Soho": "Palermo",
            "Palermo Chico": "Palermo",
            "Palermo Viejo": "Palermo",
            "Palermo Nuevo": "Palermo",
            "Barrio Norte": "Recoleta",
            "Abasto": "Balvanera",
            "Once": "Balvanera",
            "Congreso": "Monserrat",
            "Tribunales": "San Nicolás",
            "San Nicolás": "San Nicolás",
            "San Nicolas": "San Nicolás",
            "Centro": "San Nicolás",
            "Microcentro": "San Nicolás",
            "Villa Mitre": "Villa General Mitre",
            "Paternal": "La Paternal",
            "Parque Centenario": "Caballito",
            "Agronomía": "Agronomía", "Agronomia": "Agronomía",
            "Almagro": "Almagro",
            "Balvanera": "Balvanera",
            "Barracas": "Barracas",
            "Belgrano": "Belgrano",
            "Boedo": "Boedo",
            "Caballito": "Caballito",
            "Chacarita": "Chacarita",
            "Coghlan": "Coghlan",
            "Colegiales": "Colegiales",
            "Constitución": "Constitución", "Constitucion": "Constitución",
            "Flores": "Flores",
            "Floresta": "Floresta",
            "La Boca": "La Boca",
            "La Paternal": "La Paternal",
            "Liniers": "Liniers",
            "Mataderos": "Mataderos",
            "Monte Castro": "Monte Castro",
            "Monserrat": "Monserrat",
            "Nueva Pompeya": "Nueva Pompeya", "Pompeya": "Nueva Pompeya",
            "Núñez": "Núñez", "Nunez": "Núñez",
            "Palermo": "Palermo",
            "Parque Avellaneda": "Parque Avellaneda",
            "Parque Chacabuco": "Parque Chacabuco",
            "Parque Chas": "Parque Chas",
            "Parque Patricios": "Parque Patricios",
            "Puerto Madero": "Puerto Madero",
            "Recoleta": "Recoleta",
            "Retiro": "Retiro",
            "Saavedra": "Saavedra",
            "San Cristóbal": "San Cristóbal", "San Cristobal": "San Cristóbal",
            "San Telmo": "San Telmo",
            "Vélez Sarsfield": "Vélez Sarsfield", "Velez Sarsfield": "Vélez Sarsfield",
            "Versalles": "Versalles",
            "Villa Crespo": "Villa Crespo",
            "Villa del Parque": "Villa del Parque",
            "Villa Devoto": "Villa Devoto",
            "Villa General Mitre": "Villa General Mitre",
            "Villa Lugano": "Villa Lugano",
            "Villa Luro": "Villa Luro",
            "Villa Ortúzar": "Villa Ortúzar", "Villa Ortuzar": "Villa Ortúzar",
            "Villa Pueyrredón": "Villa Pueyrredón", "Villa Pueyrredon": "Villa Pueyrredón",
            "Villa Real": "Villa Real",
            "Villa Riachuelo": "Villa Riachuelo",
            "Villa Santa Rita": "Villa Santa Rita",
            "Villa Soldati": "Villa Soldati",
            "Villa Urquiza": "Villa Urquiza"
        }

        direccion_raw = raw_dict.get("direccion_raw") or raw_dict.get("direccion") or ""
        direccion = str(direccion_raw).strip() if direccion_raw and str(direccion_raw).strip() not in ["None", "nan"] else None
        titulo_input = str(raw_dict.get("titulo_aviso") or "").strip()
        url_input = str(raw_dict.get("url_publicacion") or "").strip()

        if not direccion or any(kw in str(direccion).upper() for kw in ["DEPARTAMENTO", "VENTA", "ALQUILER", "PH EN"]):
            direccion = None
            if "SANTA ROSA" in titulo_input.upper():
                direccion = "Santa Rosa 5100"
            elif "ARAOZ" in titulo_input.upper():
                direccion = "Araoz 1268"
            elif url_input and "departamento-en-venta-en-" in url_input:
                part = url_input.split("departamento-en-venta-en-")[-1].split("--")[0]
                parts_url = [p.capitalize() for p in part.split("-") if p not in ["1", "2", "3", "4", "5", "6", "ambiente", "ambientes"]]
                if parts_url:
                    direccion = " ".join(parts_url)
            
            if not direccion and titulo_input:
                calle_match = re.search(r"((?:Av\.?|Avenida|Calle)?\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9]+){1,4})", titulo_input)
                if calle_match:
                    cand_dir = calle_match.group(1).strip()
                    if not any(kw in cand_dir.upper() for kw in ["DEPARTAMENTO", "VENTA", "ALQUILER", "EXCELENTE", "HERMOSO", "UBICADO EN"]):
                        direccion = cand_dir
                if not direccion:
                    direccion = titulo_input[:60]

        barrio_input = raw_dict.get("barrio_raw") or raw_dict.get("barrio") or ""
        combined_sources = f"{barrio_input} | {direccion or ''} | {titulo_input}"
        barrio = None

        MAPEO_CALLES = {
            "Victor Martinez": "Caballito", "Santa Fe": "Recoleta", "Santa fe": "Recoleta", "Chenaut": "Palermo",
            "Migueletes": "Palermo", "Arce": "Palermo", "Maure": "Palermo", "San Blas": "Villa Luro",
            "Juan Agustin Garcia": "Villa General Mitre", "Elpidio Gonzalez": "Villa del Parque", "Condarco": "Villa del Parque",
            "Cervantes": "Villa Luro", "Montevideo": "Recoleta", "Parana": "Recoleta", "Rodriguez Pena": "Recoleta",
            "Rivadavia": "Balvanera", "Sarmiento": "San Nicolás", "Peron": "San Nicolás", "Esmeralda": "San Nicolás",
            "Galicia": "Villa General Mitre", "Laprida": "Recoleta", "French": "Recoleta", "Larrea": "Recoleta",
            "Junin": "Recoleta", "Luis Maria Campos": "Palermo", "Juan Bautista Justo": "Palermo", "Florida": "San Nicolás",
            "Lavalle": "San Nicolás", "Barrio Parque": "Recoleta", "Botnico": "Palermo", "Botanico": "Palermo",
            "Soldado De La Independencia": "Palermo", "Virrey Cevallos": "Monserrat", "Scalabrini Ortiz": "Palermo",
            "Callao": "Recoleta", "Libertador": "Palermo", "Artigas": "Villa General Mitre", "Charcas": "Palermo",
            "Viamonte": "San Nicolás", "Paraguay": "Recoleta", "San Luis": "Balvanera", "Nogoya": "Villa del Parque",
            "Nogoyá": "Villa del Parque", "Venezuela": "Balvanera", "La Pampa": "Belgrano", "Pichincha": "San Cristóbal",
            "Cuenca": "Villa del Parque", "Maipu": "Retiro", "Maipú": "Retiro"
        }

        def remove_accents(text_str: str) -> str:
            replacements = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"))
            s = text_str.lower()
            for a, b in replacements:
                s = s.replace(a, b)
            return s

        norm_sources = remove_accents(combined_sources)
        full_text_check = remove_accents(f"{combined_sources} {descripcion_cruda}")

        # Descarte estricto de inmuebles fuera de CABA (Córdoba, Miami, GBA, etc.)
        NON_CABA_KEYWORDS = [
            "cordoba", "coba", "miami", "florida", "biscayne", "brickell", "rosario",
            "mendoza", "la plata", "mar del plata", "san isidro", "vicente lopez", "olivos",
            "tigre", "avellaneda", "lanus", "quilmes", "moron", "san martin", "pilar", "escobar"
        ]
        for non_caba in NON_CABA_KEYWORDS:
            # Excepción: si 'cordoba' es la Avenida Córdoba de CABA (ej: 'av cordoba', 'av. cordoba', 'avenida cordoba')
            if non_caba == "cordoba":
                if re.search(r"\bcordoba\b", full_text_check) and not re.search(r"\b(?:av\.?|avenida)\s+cordoba\b", full_text_check):
                    raise ValueError(f"Publicación {raw_dict.get('id_publicacion')} omitida: inmueble ubicado en Córdoba (fuera de CABA).")
            elif re.search(r"\b" + re.escape(non_caba) + r"\b", full_text_check):
                raise ValueError(f"Publicación {raw_dict.get('id_publicacion')} omitida: inmueble ubicado en {non_caba.capitalize()} (fuera de CABA).")

        for kw_zone, b_oficial in MAPEO_BARRIOS.items():
            norm_kw = remove_accents(kw_zone)
            if re.search(r"\b" + re.escape(norm_kw) + r"\b", norm_sources):
                barrio = b_oficial
                break

        if not barrio and direccion:
            norm_dir = remove_accents(direccion)
            for calle_kw, b_oficial in MAPEO_CALLES.items():
                norm_calle = remove_accents(calle_kw)
                if re.search(r"\b" + re.escape(norm_calle) + r"\b", norm_dir):
                    barrio = b_oficial
                    break

        if not barrio:
            raise ValueError(f"Publicación {raw_dict.get('id_publicacion')} omitida: no se detectó un barrio oficial de CABA válido (fuera de CABA o no reconocido).")

        raw_titulo = raw_dict.get("titulo_aviso")
        titulo_aviso = str(raw_titulo)[:250] if raw_titulo else None

        cleaned_dict = {
            "id_publicacion": str(raw_dict.get("id_publicacion")),
            "portal": raw_dict.get("portal", "Zonaprop"),
            "titulo_aviso": titulo_aviso,
            "barrio": barrio,
            "direccion": direccion,
            "ambientes": ambientes,
            "habitaciones": habitaciones,
            "banos": banos,
            "estado_propiedad": estado_propiedad_cand,
            "precio_usd": precio_usd,
            "m2_totales": m2_totales,
            "m2_cubiertos": m2_cubiertos,
            "precio_m2": precio_m2,
            "expensas": expensas,
            "antiguedad": antiguedad,
            "disposicion": disposicion,
            "descripcion_cruda": descripcion_cruda,
            "tiene_cochera": tiene_cochera,
            "tiene_amenities": tiene_amenities,
            "desarrolladora": desarrolladora,
            "url_publicacion": raw_dict.get("url_publicacion"),
            "fecha_primera_extraccion": now,
            "fecha_ultima_actualizacion": now,
        }

        return cleaned_dict

    except Exception as e:
        logger.error(f"Error al limpiar datos del departamento {raw_dict.get('id_publicacion')}: {e}")
        raise
