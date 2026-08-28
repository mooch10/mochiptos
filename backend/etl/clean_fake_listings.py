"""
Módulo de Limpieza y Depuración de Publicaciones Falsas, Inválidas o No Departamentos.
Inspecciona la base de datos MySQL `departamentos` y purga automáticamente:
1. Publicaciones con precio irrealmente bajo (< $15.000 USD).
2. Publicaciones con cantidad de ambientes anómala (> 6 ambientes o < 1).
3. Superficies atípicas (< 10 m² o > 1.000 m²).
4. Valor de USD/m² fuera de rango realista en CABA (< 300 o > 15.000 USD/m²).
5. Inmuebles que no son departamentos (cocheras, terrenos, lotes, locales, galpones, oficinas, campos).
6. Registros fuera de los 48 barrios oficiales de CABA o pertenecientes a GBA / Provincias.
"""

import os
import sys
import re
import logging
from typing import Dict, Any, List

# Asegurar que el directorio raíz esté en sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.connection import SessionLocal
from app.db.models import Departamento

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Set de los 48 barrios oficiales de Capital Federal (CABA)
CABA_BARRIOS_SET = {
    "Palermo", "Belgrano", "Recoleta", "Caballito", "Núñez", "Almagro", "Villa Crespo",
    "Balvanera", "Villa Urquiza", "Flores", "Colegiales", "Villa Devoto", "San Telmo",
    "Puerto Madero", "Barracas", "Monserrat", "Retiro", "Saavedra", "Chacarita",
    "Coghlan", "Floresta", "La Boca", "La Paternal", "Liniers", "Mataderos",
    "Monte Castro", "Nueva Pompeya", "Parque Avellaneda", "Parque Chacabuco",
    "Parque Chas", "Parque Patricios", "San Cristóbal", "San Nicolás", "Versalles",
    "Villa del Parque", "Villa General Mitre", "Villa Lugano", "Villa Luro",
    "Villa Ortúzar", "Villa Pueyrredón", "Villa Real", "Villa Riachuelo",
    "Villa Santa Rita", "Villa Soldati", "Boedo", "Constitución", "Agronomía"
}

# Palabras clave de inmuebles no departamentales o avisos de alquiler/spam
NO_DEPTO_KEYWORDS = [
    "cochera", "cocheras", "terreno", "lote", "lotes", "local comercial", 
    "oficina", "galpon", "deposito", "campo", "fondo de comercio",
    "alquiler por dia", "alquiler temporario", "estacionamiento"
]

# Palabras clave de ubicaciones fuera de CABA
NON_CABA_KEYWORDS = [
    "gba", "gran buenos aires", "vicente lopez", "vicente lópez", "olivos",
    "san isidro", "san fernando", "tigre", "avellaneda", "lanus", "lanús",
    "quilmes", "moron", "morón", "san martin", "san martín", "ramos mejia",
    "lomas de zamora", "pilar", "escobar", "cordoba", "rosario", "mendoza",
    "mar del plata", "la plata"
]


def remove_accents(text_str: str) -> str:
    """Remueve tildes para comparación insensible a acentos."""
    if not text_str:
        return ""
    replacements = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"))
    s = text_str.lower()
    for a, b in replacements:
        s = s.replace(a, b)
    return s


def audit_and_purge_fake_listings(commit: bool = True) -> Dict[str, Any]:
    """
    Audita y purga de la base de datos MySQL todas las publicaciones falsas o no departamentales.
    """
    session = SessionLocal()
    try:
        all_deptos = session.query(Departamento).all()
        total_inicial = len(all_deptos)
        logger.info(f"Iniciando auditoría de depuración sobre {total_inicial} publicaciones en MySQL...")

        reasons_counter = {
            "precio_bajo (<15k USD)": 0,
            "ambientes_excesivos (>6 amb)": 0,
            "m2_anomalos (<10m2 o >1000m2)": 0,
            "precio_m2_anomalo (<300 o >15000)": 0,
            "palabras_clave_no_depto": 0,
            "barrio_fuera_caba": 0
        }

        to_delete = []

        for dep in all_deptos:
            reason = None

            # Rule 1: Precio sospechoso de venta (< $15.000 USD)
            if dep.precio_usd is not None and dep.precio_usd < 15000.0:
                reason = "precio_bajo (<15k USD)"

            # Rule 2: Corrección automática de monoambientes mal etiquetados o eliminación si > 6 o < 1
            full_text = remove_accents(f"{dep.titulo_aviso or ''} {dep.direccion or ''} {dep.descripcion_cruda or ''}")
            is_mono = any(kw in full_text for kw in ["monoambiente", "monambiente", "1-ambiente", "1-ambientes", "studio", "estudio"])
            if is_mono and dep.ambientes != 1:
                dep.ambientes = 1

            if dep.ambientes is not None and (dep.ambientes > 6 or dep.ambientes < 1):
                reason = "ambientes_excesivos (>6 amb)"

            # Rule 3: Metros cuadrados irreales (< 10 m² o > 1.000 m²)
            elif dep.m2_totales is not None and (dep.m2_totales < 10.0 or dep.m2_totales > 1000.0):
                reason = "m2_anomalos (<10m2 o >1000m2)"

            # Rule 4: Precio por m² fuera de rangos racionales de mercado CABA (< 300 o > 15.000 USD/m²)
            elif dep.precio_m2 is not None and (dep.precio_m2 < 300.0 or dep.precio_m2 > 15000.0):
                reason = "precio_m2_anomalo (<300 o >15000)"

            # Rule 5 & 6: Inmuebles no departamentales y ubicaciones fuera de CABA
            else:
                has_non_caba = False
                for kw in NON_CABA_KEYWORDS:
                    if kw == "cordoba":
                        if re.search(r"\bcordoba\b", full_text) and not re.search(r"\b(?:av\.?|avenida)\s+cordoba\b", full_text):
                            has_non_caba = True
                            break
                    elif re.search(r"\b" + re.escape(kw) + r"\b", full_text):
                        has_non_caba = True
                        break

                if any(re.search(r"\b" + re.escape(kw) + r"\b", full_text) for kw in NO_DEPTO_KEYWORDS):
                    reason = "palabras_clave_no_depto"
                elif has_non_caba or (dep.barrio and dep.barrio not in CABA_BARRIOS_SET):
                    reason = "barrio_fuera_caba"

            if reason:
                reasons_counter[reason] += 1
                to_delete.append(dep)

        total_purgados = len(to_delete)

        if commit:
            if total_purgados > 0:
                for dep in to_delete:
                    session.delete(dep)
                logger.info(f"✅ Depuración exitosa: {total_purgados} publicaciones falsas/inválidas eliminadas de MySQL.")
            session.commit()

        total_restantes = total_inicial - total_purgados

        summary = {
            "total_inicial": total_inicial,
            "total_purgados": total_purgados,
            "total_restantes": total_restantes,
            "desglose_por_motivo": reasons_counter
        }
        return summary

    except Exception as e:
        session.rollback()
        logger.error(f"Error durante la depuración de base de datos: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logger.info("=== EJECUTANDO LIMPIADOR DE PUBLICACIONES FALSAS E INVÁLIDAS ===")
    res = audit_and_purge_fake_listings(commit=True)
    print("\n================ RESUMEN DE DEPURACIÓN EN MYSQL ================")
    print(f"Total Inicial: {res['total_inicial']:,}")
    print(f"Total Purgados: {res['total_purgados']:,}")
    print(f"Total Válidos Restantes: {res['total_restantes']:,}")
    print("\nDesglose de Motivos de Eliminación:")
    for motive, count in res["desglose_por_motivo"].items():
        print(f"  • {motive}: {count:,}")
    print("=================================================================\n")
