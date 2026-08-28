from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
from app.analytics.financial import (
    calculate_icl_adjustment,
    calculate_ipc_adjustment,
    calculate_uva_mortgage,
    get_latest_uva_and_dolar
)

router = APIRouter(prefix="/calc", tags=["Finanzas"])

@router.get("/icl")
def get_icl_calc(
    monto_inicial: float = Query(..., description="Monto inicial del alquiler en ARS"),
    fecha_inicio: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: str = Query(..., description="Fecha de fin (YYYY-MM-DD)")
):
    """Calcula la actualización de alquiler basada en el ICL (BCRA)."""
    try:
        dt_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        res = calculate_icl_adjustment(monto_inicial, dt_inicio, dt_fin)
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en cálculo ICL: {str(e)}")

@router.get("/ipc")
def get_ipc_calc(
    monto_inicial: float = Query(..., description="Monto inicial en ARS"),
    meses: int = Query(3, description="Período de meses a evaluar (ej: 3, 6, 12)"),
    fecha_inicio: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)")
):
    """Calcula el ajuste acumulado según IPC (INDEC)."""
    try:
        dt_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        res = calculate_ipc_adjustment(monto_inicial, meses, dt_inicio)
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en cálculo IPC: {str(e)}")

@router.get("/uva")
def get_uva_sim(
    monto_usd: float = Query(..., description="Monto del préstamo en USD"),
    tna: float = Query(5.5, description="Tasa Nominal Anual %"),
    plazo_anios: int = Query(20, description="Plazo del préstamo en años")
):
    """Simula cuota inicial de crédito hipotecario UVA."""
    try:
        latest = get_latest_uva_and_dolar()
        res = calculate_uva_mortgage(
            loan_amount_usd=monto_usd,
            tna_percent=tna,
            term_years=plazo_anios,
            uva_value=latest["uva_actual"],
            dolar_blue_rate=latest["dolar_blue_actual"]
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en simulación UVA: {str(e)}")
