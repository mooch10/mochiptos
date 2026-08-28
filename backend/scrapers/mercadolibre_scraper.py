"""
Extractor de publicaciones de Mercado Libre basado estrictamente en la estructura HTML provista.
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional


def parse_mercadolibre_card(card_element: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Extrae la información cruda de una tarjeta HTML de Mercado Libre.

    Selectores basados estrictamente en el HTML provisto:
    - id_publicacion: input `input[name="id"]` -> atributo `value`, o en ausencia de este, del id de `data-id` / URL
    - url_publicacion: atributo `href` en `a.poly-component__title` o `a.poly-component__link`
    - titulo_aviso: texto en `a.poly-component__title`
    - precio_raw: combinación del símbolo (`.andes-money-amount__currency-symbol`) y la fracción (`.andes-money-amount__fraction`) dentro de `.poly-component__price`
    - direccion_raw & barrio_raw: texto dentro de `.poly-component__location`
    - features (ambientes, baños, m2): elementos `.poly-attributes_list__item` dentro de `.poly-component__attributes-list`
    """
    try:
        # 1. id_publicacion
        id_input = card_element.find("input", {"name": "id"})
        id_publicacion = None
        if id_input and id_input.get("value"):
            id_publicacion = id_input.get("value")
        
        # 2. url_publicacion & titulo_aviso
        title_a = card_element.select_one("a.poly-component__title")
        if not title_a:
            title_a = card_element.select_one("a.poly-component__link")

        url_publicacion = title_a.get("href") if title_a else None
        titulo_aviso = title_a.get_text(strip=True) if title_a else None

        # Fallback para id_publicacion desde la URL si no estuviera el input
        if not id_publicacion and url_publicacion:
            import re
            match = re.search(r"(MLA[-_]?\d+)", url_publicacion)
            if match:
                id_publicacion = match.group(1).replace("-", "")

        if not id_publicacion:
            return None

        # 3. precio_raw
        price_container = card_element.select_one(".poly-component__price")
        precio_raw = None
        if price_container:
            symbol_elem = price_container.select_one(".andes-money-amount__currency-symbol")
            fraction_elem = price_container.select_one(".andes-money-amount__fraction")
            
            symbol = symbol_elem.get_text(strip=True) if symbol_elem else ""
            fraction = fraction_elem.get_text(strip=True) if fraction_elem else ""
            
            if symbol or fraction:
                precio_raw = f"{symbol} {fraction}".strip()

        # 4. direccion_raw & barrio_raw y Validación Estricta de Ubicación (Solo CABA)
        location_elem = card_element.select_one(".poly-component__location")
        location_text = location_elem.get_text(strip=True) if location_elem else None

        # Palabras clave explícitas fuera de CABA (GBA, Provincias, etc.)
        NON_CABA_KEYWORDS = [
            "gba", "gran buenos aires", "bs.as. gba", "provincia", "vicente lopez", "vicente lópez",
            "olivos", "san isidro", "san fernando", "tigre", "avellaneda", "lanus", "lanús",
            "quilmes", "moron", "morón", "san martin", "san martín", "ramos mejia", "ramos mejía",
            "lomas de zamora", "pilar", "escobar", "cordoba", "córdoba", "rosario", "mendoza",
            "mar del plata", "uruguay", "la plata", "san justo", "ituzaingo", "ituzaingó"
        ]

        card_full_text = card_element.get_text(separator=" ", strip=True).lower()

        # Filtrar si la ubicación o texto completo indica explícitamente fuera de CABA
        if location_text:
            loc_lower = location_text.lower()
            if any(non_caba in loc_lower for non_caba in NON_CABA_KEYWORDS):
                return None

        # Filtrar si el tipo de operación es alquiler o el tipo de inmueble no es departamento
        if any(kw in card_full_text for kw in ["alquiler", "alquilo", "alquila", "por dia", "temporal"]):
            return None
        
        if any(kw in card_full_text for kw in ["terreno", "lote ", "lotes", "cochera", "local comercial", "oficina", "campo "]):
            if not any(dep in card_full_text for dep in ["depto", "departamento", "monoambiente", "ambientes", "amb."]):
                return None

        direccion_raw = None
        barrio_raw = None
        if location_text:
            parts = [p.strip() for p in location_text.split(",")]
            # Ej: Av. Gral. Las Heras 2902, Palermo, Capital Federal
            if len(parts) >= 2:
                if any(caba_kw in parts[-1].upper() for caba_kw in ["CAPITAL FEDERAL", "CABA", "BUENOS AIRES CABA"]):
                    barrio_raw = parts[-2]
                    direccion_raw = parts[0] if len(parts) > 2 else None
                else:
                    barrio_raw = parts[-1]
                    direccion_raw = parts[0]
            else:
                barrio_raw = location_text

        # Fallback de dirección: si la dirección no incluye altura y el título trae la calle/altura
        if (not direccion_raw or len(direccion_raw) < 3) and titulo_aviso:
            direccion_raw = titulo_aviso

        # 5. features (ambientes, baños, m2_totales, m2_cubiertos, antigüedad, disposición)
        attr_items = card_element.select(".poly-component__attributes-list .poly-attributes_list__item")
        attr_texts = [item.get_text(strip=True) for item in attr_items]

        m2_totales_raw = None
        m2_cubiertos_raw = None
        ambientes_raw = None
        habitaciones_raw = None
        banos_raw = None
        estado_propiedad = None
        antiguedad_raw = None
        disposicion_raw = None

        for text in attr_texts:
            text_lower = text.lower()
            if "m² cub" in text_lower or "m2 cub" in text_lower or "cubierto" in text_lower:
                m2_cubiertos_raw = text
            elif "m² tot" in text_lower or "m²" in text_lower or "m2" in text_lower:
                m2_totales_raw = text
            elif "amb" in text_lower:
                ambientes_raw = text
            elif "dorm" in text_lower or "hab" in text_lower:
                habitaciones_raw = text
            elif "baño" in text_lower or "bano" in text_lower:
                banos_raw = text
            elif any(e in text_lower for e in ["pozo", "estrenar", "usado", "año"]):
                antiguedad_raw = text
            elif any(d in text_lower for d in ["frente", "contrafrente", "lateral", "interno"]):
                disposicion_raw = text

        # Normalizar estado_propiedad estrictamente ('pozo', 'a estrenar', 'usado')
        if any(kw in card_full_text for kw in ["pozo", "en pozo", "en construccion", "en construcción"]):
            estado_propiedad = "pozo"
        elif any(kw in card_full_text for kw in ["a estrenar", "estrenar"]):
            estado_propiedad = "a estrenar"
        else:
            estado_propiedad = "usado"

        # Expensas en Mercado Libre (ej: .poly-component__maintenance-fee)
        exp_elem = card_element.select_one(".poly-component__maintenance-fee, .poly-component__expenses")
        expensas_raw = exp_elem.get_text(strip=True) if exp_elem else None

        # descripcion_cruda (texto íntegro de la publicación)
        descripcion_cruda = card_element.get_text(separator=" ", strip=True)

        # 6. Retorno de diccionario crudo
        return {
            "id_publicacion": str(id_publicacion),
            "portal": "Mercado Libre",
            "titulo_aviso": titulo_aviso,
            "barrio_raw": barrio_raw,
            "direccion_raw": direccion_raw,
            "ambientes_raw": ambientes_raw,
            "habitaciones_raw": habitaciones_raw,
            "banos_raw": banos_raw,
            "estado_propiedad": estado_propiedad,
            "antiguedad_raw": antiguedad_raw,
            "disposicion_raw": disposicion_raw,
            "precio_raw": precio_raw,
            "expensas_raw": expensas_raw,
            "m2_totales_raw": m2_totales_raw,
            "m2_cubiertos_raw": m2_cubiertos_raw,
            "descripcion_cruda": descripcion_cruda,
            "url_publicacion": url_publicacion,
        }

    except Exception as e:
        print(f"Error parseando tarjeta de Mercado Libre: {e}")
        return None

    except Exception as e:
        print(f"Error parseando tarjeta de Mercado Libre: {e}")
        return None


def parse_mercadolibre_page(html_content: str) -> List[Dict[str, Any]]:
    """
    Parsea una página completa o fragmento HTML de listado de Mercado Libre.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    cards = soup.find_all(class_=lambda c: c and ("poly-card" in c or "ui-search-result__wrapper" in c))
    
    seen_ids = set()
    results = []

    for card in cards:
        # Descartar banners de emprendimientos globales en pozo
        tag_badge = card.select_one(".poly-component__highlight, .poly-component__badge")
        if tag_badge and "EMPRENDIMIENTO" in tag_badge.get_text(strip=True).upper():
            continue

        parsed = parse_mercadolibre_card(card)
        if parsed and parsed["id_publicacion"] not in seen_ids:
            seen_ids.add(parsed["id_publicacion"])
            results.append(parsed)

    return results
