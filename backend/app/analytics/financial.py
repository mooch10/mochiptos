import os
import io
import logging
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

BCRA_ICL_URL = "https://www.bcra.gob.ar/Pdfs/PublicacionesEstadisticas/diar_icl.xls"
ARGENTINA_DATOS_IPC_URL = "https://api.argentinadatos.com/v1/finanzas/indices/inflacion"
ARGENTINA_DATOS_UVA_URL = "https://api.argentinadatos.com/v1/finanzas/indices/uva"
DOLAR_API_BLUE_URL = "https://dolarapi.com/v1/dolares/blue"

# 1. ICL
def fetch_icl_series() -> pd.DataFrame:
    cache_path = os.path.join(os.path.dirname(__file__), "icl_cache.csv")
    try:
        response = requests.get(
            BCRA_ICL_URL,
            verify=False,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        response.raise_for_status()
        df_raw = pd.read_excel(io.BytesIO(response.content), engine="xlrd")

        clean_data = []
        for idx, row in df_raw.iterrows():
            val1 = row.iloc[0]
            val2 = row.iloc[1]
            try:
                dt = pd.to_datetime(val1, errors="coerce", dayfirst=True)
                num = float(val2)
                if pd.notna(dt) and pd.notna(num) and num > 0:
                    clean_data.append({"fecha": dt.date(), "valor": num})
            except Exception:
                continue

        df_clean = pd.DataFrame(clean_data).sort_values("fecha").reset_index(drop=True)
        if not df_clean.empty:
            try:
                df_clean.to_csv(cache_path, index=False)
            except Exception:
                pass
            return df_clean
    except Exception as e:
        logger.warning(f"Conexión BCRA fallida ({e}). Usando cache local.")

    if os.path.exists(cache_path):
        try:
            df_cache = pd.read_csv(cache_path)
            df_cache["fecha"] = pd.to_datetime(df_cache["fecha"]).dt.date
            df_cache["valor"] = pd.to_numeric(df_cache["valor"], errors="coerce")
            return df_cache.dropna().sort_values("fecha").reset_index(drop=True)
        except Exception as e:
            logger.error(f"Error cache ICL: {e}")

    return pd.DataFrame(columns=["fecha", "valor"])


def calculate_icl_adjustment(initial_amount: float, start_date: datetime.date, end_date: datetime.date, df_icl: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    if df_icl is None or df_icl.empty:
        df_icl = fetch_icl_series()

    if df_icl.empty:
        raise ValueError("Serie ICL no disponible actualmente.")

    row_start = df_icl[df_icl["fecha"] <= start_date].tail(1)
    if row_start.empty:
        row_start = df_icl.head(1)

    row_end = df_icl[df_icl["fecha"] <= end_date].tail(1)
    if row_end.empty:
        row_end = df_icl.tail(1)

    icl_start = float(row_start["valor"].values[0])
    icl_end = float(row_end["valor"].values[0])
    date_start_found = row_start["fecha"].values[0]
    date_end_found = row_end["fecha"].values[0]

    factor = icl_end / icl_start
    updated_amount = round(initial_amount * factor, 2)
    percentage_increase = round((factor - 1.0) * 100, 2)

    return {
        "monto_inicial": initial_amount,
        "monto_actualizado": updated_amount,
        "porcentaje_aumento": percentage_increase,
        "icl_inicio": icl_start,
        "icl_fin": icl_end,
        "fecha_inicio_usada": str(date_start_found),
        "fecha_fin_usada": str(date_end_found),
    }


# 2. IPC
def fetch_ipc_series() -> pd.DataFrame:
    try:
        r = requests.get(ARGENTINA_DATOS_IPC_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        return df.dropna().sort_values("fecha").reset_index(drop=True)
    except Exception as e:
        logger.error(f"Error API IPC: {e}")
        return pd.DataFrame(columns=["fecha", "valor"])


def calculate_ipc_adjustment(initial_amount: float, months_period: int, start_date: datetime.date, df_ipc: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    if df_ipc is None or df_ipc.empty:
        df_ipc = fetch_ipc_series()

    if df_ipc.empty:
        raise ValueError("Serie IPC no disponible actualmente.")

    sub_df = df_ipc[df_ipc["fecha"] >= start_date].head(months_period)
    if sub_df.empty:
        sub_df = df_ipc.tail(months_period)

    accumulated_factor = 1.0
    detailed_months = []
    for _, row in sub_df.iterrows():
        monthly_val = float(row["valor"])
        accumulated_factor *= (1.0 + (monthly_val / 100.0))
        detailed_months.append({"fecha": str(row["fecha"]), "ipc_mensual": monthly_val})

    updated_amount = round(initial_amount * accumulated_factor, 2)
    percentage_increase = round((accumulated_factor - 1.0) * 100, 2)

    return {
        "monto_inicial": initial_amount,
        "monto_actualizado": updated_amount,
        "porcentaje_aumento": percentage_increase,
        "meses_evaluados": len(sub_df),
        "detalle_meses": detailed_months
    }


# 3. UVA / Hipotecario
def fetch_uva_series() -> pd.DataFrame:
    try:
        r = requests.get(ARGENTINA_DATOS_UVA_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        return df.dropna().sort_values("fecha").reset_index(drop=True)
    except Exception as e:
        logger.error(f"Error API UVA: {e}")
        return pd.DataFrame(columns=["fecha", "valor"])


def get_latest_uva_and_dolar() -> Dict[str, float]:
    uva_val = 1250.0
    dolar_val = 1350.0
    try:
        df_uva = fetch_uva_series()
        if not df_uva.empty:
            uva_val = float(df_uva.iloc[-1]["valor"])
    except Exception:
        pass

    try:
        r = requests.get(DOLAR_API_BLUE_URL, timeout=5)
        if r.status_code == 200:
            dolar_val = float(r.json().get("venta", dolar_val))
    except Exception:
        pass

    return {"uva_actual": uva_val, "dolar_blue_actual": dolar_val}


def calculate_uva_mortgage(
    loan_amount_usd: float,
    tna_percent: float,
    term_years: int,
    uva_value: float,
    dolar_blue_rate: float
) -> Dict[str, Any]:
    loan_amount_ars = loan_amount_usd * dolar_blue_rate
    loan_amount_uva = loan_amount_ars / uva_value if uva_value > 0 else 0.0

    total_months = term_years * 12
    monthly_rate = (tna_percent / 100.0) / 12.0

    if monthly_rate > 0:
        pmt_uva = loan_amount_uva * (monthly_rate * ((1 + monthly_rate) ** total_months)) / (((1 + monthly_rate) ** total_months) - 1)
    else:
        pmt_uva = loan_amount_uva / total_months if total_months > 0 else 0.0

    pmt_ars = pmt_uva * uva_value
    pmt_usd = pmt_ars / dolar_blue_rate if dolar_blue_rate > 0 else 0.0

    return {
        "monto_prestamo_usd": loan_amount_usd,
        "monto_prestamo_ars": loan_amount_ars,
        "monto_prestamo_uva": loan_amount_uva,
        "cuota_inicial_uva": round(pmt_uva, 2),
        "cuota_inicial_ars": round(pmt_ars, 2),
        "cuota_inicial_usd": round(pmt_usd, 2),
        "plazo_meses": total_months,
        "tasa_tna": tna_percent,
        "valor_uva_usado": uva_value,
        "dolar_usado": dolar_blue_rate
    }
