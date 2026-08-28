import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

REPORTE_INMOBILIARIO_URL = "https://www.reporteinmobiliario.com/novedades"

def scrape_reporte_inmobiliario_news(limit: int = 5) -> List[Dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/"
    }
    
    news_items = []
    try:
        response = requests.get(REPORTE_INMOBILIARIO_URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Buscar artículos o notas en la estructura HTML
        articles = soup.find_all(["article", "div"], class_=lambda c: c and ("nota" in c or "article" in c or "card" in c or "post" in c or "item" in c))
        
        if not articles:
            # Fallback general para enlaces dentro del contenedor de novedades
            articles = soup.find_all("a", href=True)

        for art in articles:
            if len(news_items) >= limit:
                break

            title_elem = art.find(["h1", "h2", "h3", "h4", "strong"])
            if not title_elem and art.name == "a":
                title_text = art.get_text(strip=True)
            elif title_elem:
                title_text = title_elem.get_text(strip=True)
            else:
                continue

            if not title_text or len(title_text) < 10:
                continue

            # Link original
            link = art.get("href") if art.name == "a" else None
            if not link:
                a_tag = art.find("a", href=True)
                if a_tag:
                    link = a_tag.get("href")

            if link and not link.startswith("http"):
                link = f"https://www.reporteinmobiliario.com{link}"

            # Resumen / Bajada
            summary_elem = art.find(["p", "span", "div"], class_=lambda c: c and ("resumen" in c or "bajada" in c or "excerpt" in c or "text" in c))
            summary_text = summary_elem.get_text(strip=True) if summary_elem else "Sin resumen disponible."

            news_items.append({
                "titulo": title_text,
                "resumen": summary_text,
                "link": link or REPORTE_INMOBILIARIO_URL
            })

    except Exception as e:
        # Retornar lista vacía o fallback informativo en caso de fallo de red
        news_items.append({
            "titulo": "Servicio de novedades inmobiliarias temporalmente no disponible",
            "resumen": f"No se pudo completar el scraping en tiempo real: {str(e)}",
            "link": REPORTE_INMOBILIARIO_URL
        })

    return news_items[:limit]
