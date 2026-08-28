"""
Extractor de publicaciones de Argenprop basado estrictamente en la estructura HTML provista.
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional


def parse_argenprop_card(card_element: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Extrae la información cruda de una tarjeta HTML de Argenprop.

    Selectores basados estrictamente en el HTML provisto:
    - id_publicacion: atributo `data-aviso-id` (ej. en `[data-aviso-id]`) o `data-favourite`
    - url_publicacion: construido como `https://www.argenprop.com/inmueble-{id_publicacion}` o extraído de `a.card`
    - precio_raw: texto dentro de `.card__price`
    - direccion_raw: texto dentro de `.card__address`
    - barrio_raw: texto dentro de `.card__title--primary`
    - titulo_aviso: texto dentro de `.card__title`
    - features (m2_totales, dormitorios/habitaciones, antigüedad/estado): items `<span>` dentro de `.card__main-features li`
    """
    try:
        # 1. id_publicacion
        id_elem = card_element.find(attrs={"data-aviso-id": True})
        if not id_elem:
            id_elem = card_element.find(attrs={"data-favourite": True})
        
        id_publicacion = None
        if id_elem:
            id_publicacion = id_elem.get("data-aviso-id") or id_elem.get("data-favourite")

        if not id_publicacion:
            return None

        # 2. url_publicacion
        # Si el elemento o un ancestro/padre tiene un enlace <a> con href
        a_tag = card_element.find_parent("a") or card_element.find("a", href=True)
        if a_tag and a_tag.get("href"):
            href = a_tag.get("href")
            url_publicacion = f"https://www.argenprop.com{href}" if href.startswith("/") else href
        else:
            url_publicacion = f"https://www.argenprop.com/inmueble-{id_publicacion}"

        # 3. precio_raw y expensas_raw
        price_elem = card_element.select_one(".card__price")
        precio_raw = None
        expensas_raw = None
        if price_elem:
            exp_elem = price_elem.select_one(".card__expenses") or card_element.select_one(".card__expenses")
            if exp_elem:
                expensas_raw = exp_elem.get_text(strip=True)

            # Clonamos para eliminar temporalmente los elementos secundarias como expensas
            price_elem_copy = BeautifulSoup(str(price_elem), "html.parser")
            for expenses in price_elem_copy.select(".card__expenses"):
                expenses.decompose()
            precio_raw = price_elem_copy.get_text(separator=" ", strip=True)

        # 4. direccion_raw (extraer de .card__address o atributo data-card-direccion)
        address_elem = card_element.select_one(".card__address")
        direccion_raw = None
        if address_elem:
            direccion_raw = address_elem.get("data-card-direccion") or address_elem.get_text(strip=True)
            if not direccion_raw or len(direccion_raw) < 2:
                direccion_raw = address_elem.get_text(strip=True)

        # 5. barrio_raw (aislar nombre exacto del barrio desestimando la frase completa)
        title_primary = card_element.select_one(".card__title--primary")
        barrio_raw = None
        if title_primary:
            primary_text = title_primary.get_text(strip=True)
            # Ejemplos: "Departamento en Venta en Palermo Hollywood, Palermo" -> "Palermo"
            if " en " in primary_text:
                after_en = primary_text.split(" en ")[-1].strip()
                subparts = [p.strip() for p in after_en.split(",")]
                candidate = subparts[-1] if subparts else after_en
                # Validar que no vuelva a contener la frase del título
                if "DEPARTAMENTO" not in candidate.upper() and "VENTA" not in candidate.upper():
                    barrio_raw = candidate
            elif "," in primary_text:
                candidate = primary_text.split(",")[-1].strip()
                if "DEPARTAMENTO" not in candidate.upper() and "VENTA" not in candidate.upper():
                    barrio_raw = candidate

        # 6. titulo_aviso & descripcion_cruda
        title_elem = card_element.select_one(".card__title")
        titulo_aviso = title_elem.get_text(strip=True) if title_elem else None

        desc_elem = card_element.select_one(".card__info, .card__description, .card__details-box")
        if desc_elem:
            descripcion_cruda = desc_elem.get_text(separator=" ", strip=True)
        else:
            descripcion_cruda = card_element.get_text(separator=" ", strip=True)

        # 7. main-features (m2_totales, m2_cubiertos, dormitorios, antigüedad, disposición)
        features_spans = card_element.select(".card__main-features li span, .card__main-features li")
        features_text = [span.get_text(strip=True) for span in features_spans]

        m2_totales_raw = None
        m2_cubiertos_raw = None
        ambientes_raw = None
        habitaciones_raw = None
        estado_propiedad = None
        antiguedad_raw = None
        disposicion_raw = None

        for text in features_text:
            text_lower = text.lower()
            if "m² cub" in text_lower or "m2 cub" in text_lower or "cubie" in text_lower:
                m2_cubiertos_raw = text
            elif "m² tot" in text_lower or "m²" in text_lower or "m2" in text_lower:
                m2_totales_raw = text
            elif "amb" in text_lower:
                ambientes_raw = text
            elif "dorm" in text_lower or "hab" in text_lower:
                habitaciones_raw = text
            elif "año" in text_lower or "estrenar" in text_lower or "pozo" in text_lower:
                estado_propiedad = text
                antiguedad_raw = text
            elif any(d in text_lower for d in ["frente", "contrafrente", "lateral", "interno"]):
                disposicion_raw = text

        # 8. Retorno de diccionario crudo alineado con el esquema del pipeline
        return {
            "id_publicacion": str(id_publicacion),
            "portal": "Argenprop",
            "titulo_aviso": titulo_aviso,
            "barrio_raw": barrio_raw,
            "direccion_raw": direccion_raw,
            "ambientes_raw": ambientes_raw,
            "habitaciones_raw": habitaciones_raw,
            "banos_raw": None,
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
        print(f"Error parseando tarjeta de Argenprop: {e}")
        return None


def parse_argenprop_page(html_content: str) -> List[Dict[str, Any]]:
    """
    Parsea una página completa o fragmento HTML de listado de Argenprop.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Busca por contenedor de tarjeta o contenedor de detalles
    cards = soup.find_all(class_=lambda c: c and ("card__details-box" in c or "listing__item" in c or "card" in c))
    
    # Filtro para evitar duplicados si los selectores se solapan
    seen_ids = set()
    results = []

    for card in cards:
        parsed = parse_argenprop_card(card)
        if parsed and parsed["id_publicacion"] not in seen_ids:
            seen_ids.add(parsed["id_publicacion"])
            results.append(parsed)

    return results
