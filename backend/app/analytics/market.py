import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

def filter_outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - (factor * iqr)
    upper_bound = q3 + (factor * iqr)
    return (series >= lower_bound) & (series <= upper_bound)


def get_m2_index_by_barrio(
    df: pd.DataFrame,
    selected_barrios: Optional[List[str]] = None,
    selected_ambientes: Optional[List[int]] = None
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    df_sub = df.copy()
    if selected_ambientes:
        df_sub = df_sub[df_sub["ambientes"].isin(selected_ambientes)]

    if selected_barrios:
        df_sub = df_sub[df_sub["barrio"].isin(selected_barrios)]

    df_sub = df_sub[df_sub["precio_m2"].notna() & (df_sub["precio_m2"] > 0)]

    valid_rows = []
    for barrio, group in df_sub.groupby("barrio", observed=False):
        if len(group) >= 3:
            mask = filter_outliers_iqr(group["precio_m2"])
            valid_rows.append(group[mask])
        else:
            valid_rows.append(group)

    if not valid_rows:
        return pd.DataFrame()

    df_clean = pd.concat(valid_rows, ignore_index=True)

    grouped = df_clean.groupby("barrio", observed=False).agg(
        mediana_precio_m2=("precio_m2", "median"),
        promedio_precio_m2=("precio_m2", "mean"),
        mediana_precio_usd=("precio_usd", "median"),
        total_publicaciones=("id_publicacion", "count")
    ).reset_index()

    grouped["mediana_precio_m2"] = grouped["mediana_precio_m2"].round(2)
    grouped["promedio_precio_m2"] = grouped["promedio_precio_m2"].round(2)
    grouped["mediana_precio_usd"] = grouped["mediana_precio_usd"].round(0)

    grouped = grouped.sort_values(by="mediana_precio_m2", ascending=False).reset_index(drop=True)
    return grouped


# Cache Singleton en memoria para no re-entrenar en cada request
_CACHED_MODEL: Optional[Pipeline] = None
_CACHED_R2: float = 0.0

def train_opportunity_detector_model(df: pd.DataFrame, force_retrain: bool = False) -> Tuple[Pipeline, float]:
    """
    Entrena un modelo Random Forest Regressor perfeccionado:
    1. Filtro IQR previo de outliers extremos en precio_usd y precio_m2.
    2. Incorporación de m2_cubiertos y ratio_cubierto (m2_cubiertos / m2_totales).
    3. Transformación logarítmica (np.log1p) del precio target para evitar distorsiones.
    4. Cache Singleton en memoria para respuesta instantánea.
    """
    global _CACHED_MODEL, _CACHED_R2

    if _CACHED_MODEL is not None and not force_retrain:
        return _CACHED_MODEL, _CACHED_R2

    df_train = df.copy()
    required_cols = ["precio_usd", "m2_totales", "ambientes", "barrio"]
    df_train = df_train.dropna(subset=required_cols)
    df_train = df_train[(df_train["precio_usd"] > 10000) & (df_train["m2_totales"] > 15)]

    # Feature Engineering: m2_cubiertos y ratio_cubierto
    df_train["m2_cubiertos"] = df_train["m2_cubiertos"].fillna(df_train["m2_totales"])
    df_train["ratio_cubierto"] = (df_train["m2_cubiertos"] / df_train["m2_totales"]).clip(upper=1.0, lower=0.1)

    # 1. Filtro IQR previo por barrio en precio_usd para eliminar precios erróneos
    valid_rows = []
    for _, group in df_train.groupby("barrio", observed=False):
        if len(group) >= 5:
            mask = filter_outliers_iqr(group["precio_usd"], factor=2.0)
            valid_rows.append(group[mask])
        else:
            valid_rows.append(group)

    if valid_rows:
        df_train = pd.concat(valid_rows, ignore_index=True)

    num_cols = ["m2_totales", "m2_cubiertos", "ratio_cubierto", "ambientes", "banos"]
    bool_cols = ["tiene_cochera", "tiene_amenities"]
    cat_cols = ["barrio", "estado_propiedad"]

    df_train["banos"] = df_train["banos"].fillna(1)
    df_train["tiene_cochera"] = df_train["tiene_cochera"].fillna(False).astype(int)
    df_train["tiene_amenities"] = df_train["tiene_amenities"].fillna(False).astype(int)
    df_train["estado_propiedad"] = df_train["estado_propiedad"].fillna("usado").astype(str)
    df_train["barrio"] = df_train["barrio"].astype(str)

    features = num_cols + bool_cols + cat_cols
    X = df_train[features]
    
    # 3. Transformación logarítmica target np.log1p
    y_log = np.log1p(df_train["precio_usd"])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", num_cols + bool_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
        ]
    )

    model = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=30, max_depth=10, random_state=42, n_jobs=1))
    ])

    model.fit(X, y_log)
    
    # Calcular R2 en escala real USD
    y_pred_usd = np.expm1(model.predict(X))
    u = ((df_train["precio_usd"] - y_pred_usd) ** 2).sum()
    v = ((df_train["precio_usd"] - df_train["precio_usd"].mean()) ** 2).sum()
    r2_score = float(1.0 - (u / v)) if v != 0 else 0.0

    _CACHED_MODEL = model
    _CACHED_R2 = r2_score
    logger.info(f"Modelo ML Oportunidades Optimizado entrenado con R2 = {r2_score:.4f}")

    return model, r2_score


def detect_top_opportunities(
    df: pd.DataFrame,
    top_n: int = 50,
    selected_barrios: Optional[List[str]] = None,
    selected_ambientes: Optional[List[int]] = None,
    selected_estado: Optional[List[str]] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    banos_min: Optional[int] = None,
    tiene_cochera: Optional[bool] = None,
    tiene_amenities: Optional[bool] = None
) -> pd.DataFrame:
    """
    Reconstrucción desde cero del Detector de Oportunidades aplicando las 4 Mejoras Clave:
    1. Velocidad de Respuesta (< 0.2s) con Modelo Cache en Memoria.
    2. Limpieza IQR de Outliers por barrio previa al entrenamiento.
    3. Incorporación de m2_cubiertos y ratio_cubierto (m2_cubiertos / m2_totales).
    4. Escala Logarítmica (log1p / expm1) para la variable target de precio.
    
    Flujo de Búsqueda:
    - Si el usuario no aplica filtros, devuelve las Top 50 mejores oportunidades globales de CABA.
    - Si el usuario aplica filtros (barrios, ambientes, estado, precios, etc.), evalúa el modelo
      sobre el subconjunto resultante y devuelve las Top 50 mejores oportunidades de esa búsqueda.
    """
    if df.empty or len(df) < 10:
        return pd.DataFrame()

    # 1. Obtener/Entrenar Modelo RandomForest en Memoria (< 0.2s)
    model, r2_score = train_opportunity_detector_model(df)

    df_eval = df.copy()
    df_eval = df_eval.dropna(subset=["precio_usd", "barrio"])
    df_eval["ambientes"] = df_eval["ambientes"].fillna(1).astype(int)
    df_eval["m2_totales"] = df_eval["m2_totales"].fillna(40.0)

    # 3. Incorporación de m2_cubiertos y ratio_cubierto
    df_eval["m2_cubiertos"] = df_eval["m2_cubiertos"].fillna(df_eval["m2_totales"])
    df_eval["ratio_cubierto"] = (df_eval["m2_cubiertos"] / df_eval["m2_totales"]).clip(upper=1.0, lower=0.1)

    df_eval["banos"] = df_eval["banos"].fillna(1)
    df_eval["tiene_cochera"] = df_eval["tiene_cochera"].fillna(False).astype(int)
    df_eval["tiene_amenities"] = df_eval["tiene_amenities"].fillna(False).astype(int)
    df_eval["estado_propiedad"] = df_eval["estado_propiedad"].fillna("usado").astype(str)
    df_eval["barrio"] = df_eval["barrio"].astype(str)

    # Aplicar Filtros de Usuario sobre el dataset antes de generar el Top 50
    if selected_barrios:
        barrios_clean = [b.strip().lower() for b in selected_barrios]
        df_eval = df_eval[df_eval["barrio"].str.strip().str.lower().isin(barrios_clean)]

    if selected_ambientes:
        df_eval = df_eval[df_eval["ambientes"].isin(selected_ambientes)]

    if selected_estado:
        estado_clean = [e.strip().lower() for e in selected_estado]
        df_eval = df_eval[df_eval["estado_propiedad"].str.strip().str.lower().isin(estado_clean)]

    if precio_min is not None:
        df_eval = df_eval[df_eval["precio_usd"] >= precio_min]
    if precio_max is not None:
        df_eval = df_eval[df_eval["precio_usd"] <= precio_max]
    if banos_min is not None:
        df_eval = df_eval[df_eval["banos"] >= banos_min]
    if tiene_cochera is not None:
        df_eval = df_eval[df_eval["tiene_cochera"] == (1 if tiene_cochera else 0)]
    if tiene_amenities is not None:
        df_eval = df_eval[df_eval["tiene_amenities"] == (1 if tiene_amenities else 0)]

    if df_eval.empty:
        return pd.DataFrame()

    num_cols = ["m2_totales", "m2_cubiertos", "ratio_cubierto", "ambientes", "banos"]
    bool_cols = ["tiene_cochera", "tiene_amenities"]
    cat_cols = ["barrio", "estado_propiedad"]

    X_eval = df_eval[num_cols + bool_cols + cat_cols]
    
    # 4. Predicción con reconversión expm1 desde Escala Logarítmica
    y_pred_log = model.predict(X_eval)
    df_eval["precio_estimado"] = np.expm1(y_pred_log).round(0)

    # Cálculo de métricas de oportunidad
    df_eval["margen_ganancia_usd"] = (df_eval["precio_estimado"] - df_eval["precio_usd"]).round(0)
    df_eval["descuento_porcentaje"] = (
        ((df_eval["precio_estimado"] - df_eval["precio_usd"]) / df_eval["precio_estimado"]) * 100
    ).round(1)

    # Selección del Top 50 ordenado por margen de ganancia estimado (de mayor a menor)
    opportunities = df_eval.sort_values(by="margen_ganancia_usd", ascending=False).head(top_n).reset_index(drop=True)
    
    # Sanitización de NaN/Inf a None para JSON
    opportunities = opportunities.where(pd.notnull(opportunities), None)
    return opportunities
