# CONTEXTO DEL PROYECTO: PIPELINE INMOBILIARIO Y DASHBOARD
Actúas como un Senior Data Engineer y Python Developer. Estamos construyendo un proyecto de ETL (Extracción, Transformación y Carga) y visualización de datos de departamentos en venta en Capital Federal (CABA), Argentina.

## STACK TECNOLÓGICO
- **Lenguaje:** Python 3 (Entorno Windows 11).
- **Extracción (Scraping):** Playwright con configuraciones Stealth/Anti-bot.
- **Transformación:** Pandas y `requests` (para APIs cambiarias).
- **Base de Datos:** MySQL (Gestión mediante SQLAlchemy ORM).
- **Visualización:** Streamlit.

## FUENTES DE DATOS PERMITIDAS
Exclusivamente: Zonaprop, Argenprop y Mercado Libre.

## ESQUEMA DE BASE DE DATOS E INSTRUCCIONES DE MODELADO
La tabla principal se llama `departamentos`. ESTRICTAMENTE debes usar este esquema, no asumas ni inventes columnas nuevas:
- `id_publicacion` (String, Primary Key)
- `portal` (String - Valores permitidos: 'Zonaprop', 'Argenprop', 'Mercado Libre')
- `titulo_aviso` (String)
- `barrio` (String - Exclusivo de CABA, ej: 'Palermo', 'Recoleta')
- `direccion` (String)
- `ambientes` (Integer - Valores del 1 al 5)
- `habitaciones` (Integer)
- `banos` (Integer)
- `tiene_garage` (Boolean)
- `estado_propiedad` (String - ej: 'pozo', 'a estrenar', 'usado')
- `precio_usd` (Float)
- `m2_totales` (Float)
- `orientacion` (String)
- `precio_m2` (Float)
- `url_publicacion` (String)
- `fecha_primera_extraccion` (DateTime)
- `fecha_ultima_actualizacion` (DateTime)

## REGLAS DE NEGOCIO Y ETL (CRÍTICAS)
1. **Conversión de Moneda:** Si un aviso se scrapea en Pesos Argentinos (ARS) o con símbolo "$", la capa de transformación debe consultar una API pública (ej. DolarAPI) para obtener el tipo de cambio del día y convertirlo a dólares ANTES de insertarlo como `precio_usd`.
2. **Cálculos Automáticos:** El campo `precio_m2` no se extrae directamente, siempre se calcula en Python (`precio_usd` / `m2_totales`).
3. **Manejo de Actualizaciones (UPSERT):** En MySQL, la inserción debe manejar `ON DUPLICATE KEY UPDATE`. Si el `id_publicacion` ya existe, se actualiza `precio_usd`, `fecha_ultima_actualizacion` y el cálculo de `precio_m2`.

## DIRECTIVAS PARA EL DASHBOARD (STREAMLIT)
La UI debe permitir el análisis ágil del mercado incluyendo obligatoriamente:
- Filtro Multiselect por `barrio` (uno, varios o todos).
- Filtro numérico por `ambientes` (1 a 5).
- Filtros de rango (Min/Max) para `precio_usd`.
- Filtros booleanos/numéricos para `tiene_garage`, `habitaciones` y `banos`.

## METODOLOGÍA DE TRABAJO (REGLAS DEL AGENTE)
- **Paso a paso:** Escribe código de forma iterativa. No intentes construir todo el sistema en una sola respuesta.
- **Cero Alucinaciones HTML:** NUNCA inventes selectores CSS, XPath o estructuras HTML para los scrapers. Espera siempre a que el usuario te provea un fragmento de código HTML real de los portales antes de escribir las funciones de extracción.
- **Robustez:** Incluye siempre manejo de excepciones (`try/except`) y `logging` en los procesos de extracción y carga para que un error en una publicación no detenga todo el pipeline.
- **Ejecución de Scripts de Prueba:** NUNCA ejecutes código Python en la terminal utilizando comandos inline (`python -c "..."`). Para cualquier prueba o verificación de scripts, crea siempre un archivo `.py` temporal (ej: `scratch/temp_test.py`) y ejecútalo de forma limpia (`python scratch/temp_test.py`).
