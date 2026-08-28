"""
Extractor de publicaciones de Zonaprop basado estrictamente en selectores HTML reales.
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional


def parse_zonaprop_card(card_element: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Extrae la información de una tarjeta HTML de Zonaprop.
    
    Selectores utilizados exclusivamente de la estructura HTML provista:
    - id_publicacion: atributo `data-id` en el contenedor principal `[data-qa="posting PROPERTY"]`
    - url_publicacion: atributo `href` en `<h2 data-qa="POSTING_CARD_DESCRIPTION"] > a`
    - precio_usd: texto de `<h2 data-qa="POSTING_CARD_PRICE">`
    - features (ambientes, habitaciones, baños, m2): items `<span>` dentro de `<h3 data-qa="POSTING_CARD_FEATURES">`
    - direccion: texto de `<h4 class="...location-address...">`
    - barrio: texto de `<h4 data-qa="POSTING_CARD_LOCATION">`
    - titulo_aviso: texto del enlace en `data-qa="POSTING_CARD_DESCRIPTION"`
    """
    try:
        # id_publicacion
        id_publicacion = card_element.get("data-id")
        if not id_publicacion:
            return None

        # url_publicacion & titulo_aviso
        desc_h2 = card_element.find("h2", {"data-qa": "POSTING_CARD_DESCRIPTION"})
        url_publicacion = None
        titulo_aviso = None
        if desc_h2:
            a_tag = desc_h2.find("a")
            if a_tag:
                url_publicacion = a_tag.get("href")
                titulo_aviso = a_tag.get_text(strip=True)

        # precio_usd (texto crudo)
        price_h2 = card_element.find("h2", {"data-qa": "POSTING_CARD_PRICE"})
        precio_raw = price_h2.get_text(strip=True) if price_h2 else None

        # barrio (texto crudo, ej: "Palermo, Capital Federal")
        location_h4 = card_element.find(attrs={"data-qa": "POSTING_CARD_LOCATION"})
        if not location_h4:
            location_h4 = card_element.find(class_=lambda c: c and "location-zone" in c)
        
        barrio_raw = location_h4.get_text(strip=True) if location_h4 else None

        # direccion (texto crudo, ej: "Fray Justo Santamaria de Oro al 1700")
        address_h4 = card_element.find("h4", class_=lambda c: c and "location-address" in c)
        if not address_h4:
            address_h4 = card_element.find(attrs={"data-qa": "POSTING_CARD_ADDRESS"})
        direccion_raw = address_h4.get_text(strip=True) if address_h4 else None

        # Fallback de dirección: si la tarjeta no incluye etiqueta de dirección, tomar del título
        if not direccion_raw and titulo_aviso:
            direccion_raw = titulo_aviso

        # Fallback de barrio: Si barrio_raw no está, intentar usar la dirección o título
        if not barrio_raw and direccion_raw:
            barrio_raw = direccion_raw

        # expensas (texto crudo)
        exp_elem = card_element.find(attrs={"data-qa": "expensas"})
        if not exp_elem:
            exp_elem = card_element.find(class_=lambda c: c and "expenses" in c)
        expensas_raw = exp_elem.get_text(strip=True) if exp_elem else None

        # descripcion_cruda (texto íntegro sin HTML)
        desc_elem = card_element.find(attrs={"data-qa": "POSTING_CARD_DESCRIPTION"})
        if desc_elem:
            descripcion_cruda = desc_elem.get_text(separator=" ", strip=True)
        else:
            descripcion_cruda = card_element.get_text(separator=" ", strip=True)

        # features (m2_totales, m2_cubiertos, ambientes, habitaciones, baños, antigüedad, disposición)
        features_h3 = card_element.find("h3", {"data-qa": "POSTING_CARD_FEATURES"})
        if not features_h3:
            features_h3 = card_element.find(class_=lambda c: c and "posting-features" in c)
            
        features_spans = features_h3.find_all("span") if features_h3 else []
        features_text = [span.get_text(strip=True) for span in features_spans]

        # Mapeo inicial de características según textos presentes en las etiquetas
        m2_totales_raw = None
        m2_cubiertos_raw = None
        ambientes_raw = None
        habitaciones_raw = None
        banos_raw = None
        antiguedad_raw = None
        disposicion_raw = None

        for item in features_text:
            item_lower = item.lower()
            if "m² cub" in item_lower or "m2 cub" in item_lower:
                m2_cubiertos_raw = item
            elif "m² tot" in item_lower or "m²" in item_lower or "m2" in item_lower:
                m2_totales_raw = item
            elif "amb" in item_lower:
                ambientes_raw = item
            elif "dorm" in item_lower or "hab" in item_lower:
                habitaciones_raw = item
            elif any(b_kw in item_lower for b_kw in ["baño", "baños", "bano", "banos", "baï¿½o"]):
                banos_raw = item
            elif "año" in item_lower or "a estrenar" in item_lower or "pozo" in item_lower:
                antiguedad_raw = item
            elif any(d in item_lower for d in ["frente", "contrafrente", "lateral", "interno"]):
                disposicion_raw = item

        # Reconstruir URL completa si es relativa
        if url_publicacion and url_publicacion.startswith("/"):
            url_publicacion = f"https://www.zonaprop.com.ar{url_publicacion}"

        # Estructura del diccionario respetando la firma requerida (texto crudo)
        return {
            "id_publicacion": str(id_publicacion),
            "portal": "Zonaprop",
            "titulo_aviso": titulo_aviso,
            "barrio_raw": barrio_raw,
            "direccion_raw": direccion_raw,
            "ambientes_raw": ambientes_raw,
            "habitaciones_raw": habitaciones_raw,
            "banos_raw": banos_raw,
            "estado_propiedad": antiguedad_raw,
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
        print(f"Error parseando tarjeta de Zonaprop id={card_element.get('data-id')}: {e}")
        return None


def parse_zonaprop_page(html_content: str) -> List[Dict[str, Any]]:
    """
    Parsea una página completa de listado de Zonaprop devuelta por Playwright.
    Soporta múltiples variaciones de selectores de tarjetas principales.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    cards = soup.find_all("div", attrs={"data-qa": "posting PROPERTY"})
    if not cards:
        cards = soup.select("[data-id]")

    seen_ids = set()
    results = []
    for card in cards:
        # Omitir desarrollos / emprendimientos globales en pozo sin datos de unidad individual
        if card.get("data-qa") == "posting DEVELOPMENT" or card.get("data-posting-type") == "DEVELOPMENT":
            continue

        parsed = parse_zonaprop_card(card)
        if parsed and parsed["id_publicacion"] not in seen_ids:
            seen_ids.add(parsed["id_publicacion"])
            results.append(parsed)
            
    return results
