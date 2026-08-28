from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
from app.scrapers.news_scraper import scrape_reporte_inmobiliario_news

router = APIRouter(prefix="/news", tags=["Scraping Novedades"])

@router.get("", response_model=Dict[str, Any])
def get_latest_real_estate_news(
    limit: int = Query(5, description="Cantidad de noticias a obtener (default 5)")
):
    """Micro-scraper BeautifulSoup hacia reporteinmobiliario.com extrayendo Título, Resumen y Link."""
    try:
        news = scrape_reporte_inmobiliario_news(limit=limit)
        return {
            "status": "success",
            "count": len(news),
            "source": "reporteinmobiliario.com",
            "data": news
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en scraping de novedades: {str(e)}")
