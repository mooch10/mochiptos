import time
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional

from app.db.connection import get_db
from app.db.models import Departamento
from app.analytics.market import get_m2_index_by_barrio, detect_top_opportunities

router = APIRouter(prefix="/market", tags=["Market Analytics & ML"])

_CACHED_DF: Optional[pd.DataFrame] = None
_CACHED_DF_TIME: float = 0.0

def _fetch_deptos_df(db: Session, force_reload: bool = False) -> pd.DataFrame:
    """Consulta SQL directa usando pandas.read_sql con cache en memoria de 5 minutos (Ultra-rápido)."""
    global _CACHED_DF, _CACHED_DF_TIME
    
    current_time = time.time()
    if _CACHED_DF is not None and not force_reload and (current_time - _CACHED_DF_TIME < 300):
        return _CACHED_DF

    try:
        sql_query = """
            SELECT id_publicacion, portal, titulo_aviso, barrio, direccion, ambientes, 
                   banos, estado_propiedad, precio_usd, m2_totales, 
                   m2_cubiertos, tiene_cochera, tiene_amenities, url_publicacion 
            FROM departamentos 
            WHERE precio_usd IS NOT NULL AND m2_totales IS NOT NULL AND precio_usd > 10000 AND m2_totales > 15
            ORDER BY id_publicacion DESC
            LIMIT 25000
        """
        df = pd.read_sql(sql_query, db.bind)
        
        # Optimización de tipos de datos para reducir RAM en servidores Serverless (Free Tier 512MB)
        if not df.empty:
            df["ambientes"] = df["ambientes"].fillna(1).astype("int8")
            df["banos"] = df["banos"].fillna(1).astype("int8")
            df["precio_usd"] = df["precio_usd"].astype("float32")
            df["m2_totales"] = df["m2_totales"].astype("float32")
            if "m2_cubiertos" in df.columns:
                df["m2_cubiertos"] = df["m2_cubiertos"].astype("float32")
            if "precio_m2" in df.columns:
                df["precio_m2"] = df["precio_m2"].astype("float32")

        # Normalizar estado_propiedad para corregir codificación y sinónimos
        if "estado_propiedad" in df.columns:
            estado_map = {
                "Estrenado": "usado",
                "Usado": "usado",
                "usado": "usado",
                "A estrenar": "a estrenar",
                "a estrenar": "a estrenar",
                "En construccin": "en construccion",
                "En construcción": "en construccion",
                "en construccion": "en construccion",
                "en construcción": "en construccion"
            }
            df["estado_propiedad"] = df["estado_propiedad"].map(lambda x: estado_map.get(str(x).strip(), "usado"))

        _CACHED_DF = df
        _CACHED_DF_TIME = current_time
        return df
    except Exception as e:
        if _CACHED_DF is not None:
            return _CACHED_DF
        raise e

@router.get("/m2")
def get_market_m2(
    barrios: Optional[List[str]] = Query(None, description="Lista de barrios a filtrar"),
    ambientes: Optional[List[int]] = Query(None, description="Lista de ambientes a filtrar"),
    db: Session = Depends(get_db)
):
    """Consulta MySQL agrupando por barrio, filtrando outliers (IQR) y calculando la mediana de USD/m²."""
    try:
        df = _fetch_deptos_df(db)
        if df.empty:
            return {"status": "success", "count": 0, "data": []}
        
        result_df = get_m2_index_by_barrio(df, selected_barrios=barrios, selected_ambientes=ambientes)
        return {"status": "success", "count": len(result_df), "data": result_df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en consulta de mercado m2: {str(e)}")

@router.get("/opportunities")
def get_market_opportunities(
    top_n: int = Query(50, description="Cantidad de mejores oportunidades a retornar"),
    barrios: Optional[List[str]] = Query(None, description="Lista de barrios"),
    ambientes: Optional[List[int]] = Query(None, description="Lista de ambientes"),
    estado: Optional[List[str]] = Query(None, description="Lista de estados"),
    precio_min: Optional[float] = Query(None, description="Precio mínimo en USD"),
    precio_max: Optional[float] = Query(None, description="Precio máximo en USD"),
    banos_min: Optional[int] = Query(None, description="Mínimo de baños"),
    tiene_cochera: Optional[bool] = Query(None, description="Filtrar si tiene cochera"),
    tiene_amenities: Optional[bool] = Query(None, description="Filtrar si tiene amenities"),
    db: Session = Depends(get_db)
):
    """Modelo ML RandomForest optimizado que evalúa propiedades y retorna el Top N de oportunidades filtradas por cualquier criterio."""
    try:
        df = _fetch_deptos_df(db)
        if df.empty:
            return {"status": "success", "count": 0, "data": []}
        
        b_list = barrios if barrios else None
        a_list = ambientes if ambientes else None
        e_list = estado if estado else None

        p_min = float(precio_min) if isinstance(precio_min, (int, float)) else None
        p_max = float(precio_max) if isinstance(precio_max, (int, float)) else None
        b_min = int(banos_min) if isinstance(banos_min, int) else None
        c_bool = tiene_cochera if isinstance(tiene_cochera, bool) else None
        am_bool = tiene_amenities if isinstance(tiene_amenities, bool) else None

        opportunities_df = detect_top_opportunities(
            df,
            top_n=top_n,
            selected_barrios=b_list,
            selected_ambientes=a_list,
            selected_estado=e_list,
            precio_min=p_min,
            precio_max=p_max,
            banos_min=b_min,
            tiene_cochera=c_bool,
            tiene_amenities=am_bool
        )
        
        records = opportunities_df.to_dict(orient="records")
        import math, numpy as np
        clean_records = []
        for r in records:
            clean_r = {}
            for k, v in r.items():
                if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
                    clean_r[k] = None
                elif isinstance(v, (np.integer, int)):
                    clean_r[k] = int(v)
                elif isinstance(v, (np.floating, float)):
                    clean_r[k] = float(v)
                elif isinstance(v, (np.bool_, bool)):
                    clean_r[k] = bool(v)
                else:
                    clean_r[k] = str(v)
            clean_records.append(clean_r)

        return {"status": "success", "count": len(clean_records), "data": clean_records}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/barrios")
def get_available_barrios(db: Session = Depends(get_db)):
    """Obtiene la lista única de todos los barrios disponibles en la base de datos para el buscador."""
    try:
        stmt = select(Departamento.barrio).where(Departamento.barrio.isnot(None)).distinct().order_by(Departamento.barrio)
        results = db.scalars(stmt).all()
        return {"status": "success", "count": len(results), "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener lista de barrios: {str(e)}")

@router.get("/search")
def search_properties(
    barrios: Optional[List[str]] = Query(None, description="Filtrar por barrios"),
    ambientes: Optional[List[int]] = Query(None, description="Filtrar por cantidad de ambientes"),
    estado: Optional[List[str]] = Query(None, description="Filtrar por estado_propiedad"),
    precio_min: Optional[float] = Query(None, description="Precio mínimo USD"),
    precio_max: Optional[float] = Query(None, description="Precio máximo USD"),
    banos_min: Optional[int] = Query(None, description="Mínimo de baños"),
    tiene_cochera: Optional[bool] = Query(None, description="Con cochera"),
    tiene_amenities: Optional[bool] = Query(None, description="Con amenities"),
    limit: int = Query(100, description="Límite de resultados a retornar"),
    db: Session = Depends(get_db)
):
    """Buscador universal interactivo de propiedades en toda la base de datos con cualquier combinación de filtros."""
    try:
        stmt = select(Departamento)
        
        if isinstance(barrios, list) and len(barrios) > 0:
            stmt = stmt.where(Departamento.barrio.in_(barrios))
        elif isinstance(barrios, str):
            stmt = stmt.where(Departamento.barrio == barrios)

        if isinstance(ambientes, list) and len(ambientes) > 0:
            stmt = stmt.where(Departamento.ambientes.in_(ambientes))
        elif isinstance(ambientes, int):
            stmt = stmt.where(Departamento.ambientes == ambientes)

        if isinstance(estado, list) and len(estado) > 0:
            stmt = stmt.where(Departamento.estado_propiedad.in_(estado))
        elif isinstance(estado, str):
            stmt = stmt.where(Departamento.estado_propiedad == estado)

        if isinstance(precio_min, (int, float)):
            stmt = stmt.where(Departamento.precio_usd >= precio_min)
        if isinstance(precio_max, (int, float)):
            stmt = stmt.where(Departamento.precio_usd <= precio_max)
        if isinstance(banos_min, int):
            stmt = stmt.where(Departamento.banos >= banos_min)
        if isinstance(tiene_cochera, bool):
            stmt = stmt.where(Departamento.tiene_cochera == tiene_cochera)
        if isinstance(tiene_amenities, bool):
            stmt = stmt.where(Departamento.tiene_amenities == tiene_amenities)

        stmt = stmt.limit(limit)
        results = db.scalars(stmt).all()

        data = [
            {
                "id_publicacion": d.id_publicacion,
                "portal": d.portal,
                "titulo_aviso": d.titulo_aviso,
                "barrio": d.barrio,
                "direccion": d.direccion,
                "ambientes": d.ambientes,
                "banos": d.banos,
                "estado_propiedad": d.estado_propiedad,
                "precio_usd": d.precio_usd,
                "m2_totales": d.m2_totales,
                "m2_cubiertos": d.m2_cubiertos,
                "precio_m2": d.precio_m2,
                "expensas": d.expensas,
                "antiguedad": d.antiguedad,
                "tiene_cochera": d.tiene_cochera,
                "tiene_amenities": d.tiene_amenities,
                "url_publicacion": d.url_publicacion
            }
            for d in results
        ]

        return {"status": "success", "count": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en buscador de propiedades: {str(e)}")
