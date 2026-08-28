# 🏢 Deptos CABA - Inteligencia Inmobiliaria & ML

Plataforma integral de analítica, inteligencia inmobiliaria y machine learning diseñada para el mercado de departamentos en la Ciudad Autónoma de Buenos Aires (CABA). 

El sistema extrae, limpia y analiza en tiempo real más de **92.000 publicaciones** inmobiliarias de múltiples portales (Zonaprop, Argenprop, Mercado Libre), calcula métricas $/m² por barrio ajustadas por outliers (IQR), proyecta modelos de valoración mediante **RandomForest Regressor** y provee calculadoras financieras avanzadas (Ajustes ICL, IPC y Créditos UVA).

---

## 📐 Arquitectura del Sistema

El proyecto está estructurado en una arquitectura cliente-servidor desacoplada:

```
C:\Programas\Deptos\
├── backend/          # API REST modular (FastAPI), modelos ML, DB ORM (SQLAlchemy) y Pipelines ETL
├── frontend/         # Interfaz Web interactiva (Next.js 16 App Router, React 19, Tailwind CSS, Framer Motion)
└── README.md         # Documentación general del sistema
```

---

## ⚡ Guía de Ejecución Rápida

Para iniciar la aplicación localmente, abre dos terminales de PowerShell independientes:

### 1. Iniciar el Backend (FastAPI)

```powershell
cd C:\Programas\Deptos\backend
C:\Programas\Deptos\venv\Scripts\python.exe main.py
```
* **URL de la API**: `http://127.0.0.1:8000`
* **Documentación Swagger interactiva**: `http://127.0.0.1:8000/docs`

### 2. Iniciar el Frontend (Next.js)

```powershell
cd C:\Programas\Deptos\frontend
npm run dev
```
* **Aplicación Web**: `http://localhost:3000`

---

## 🛠️ Tecnologías y Módulos Clave

### 🐍 Backend (`/backend`)
- **FastAPI**: API REST asíncrona de alto rendimiento.
- **SQLAlchemy & PyMySQL**: Conexión y mapeo ORM hacia la base de datos MySQL en la nube (Aiven Cloud).
- **Scikit-Learn & NumPy**: Modelo **RandomForest Regressor** entrenado con transformación logarítmica (`log1p`/`expm1`) y variables de superficie (`m2_cubiertos`, `ratio_cubierto`) para la predicción de valor justo de mercado.
- **Pandas**: Procesamiento de datos analíticos en memoria y filtrado estadístico de outliers mediante el método Intercuartílico (IQR).
- **Playwright & BeautifulSoup**: Scrapers automáticos con evasión de bloqueos WAF.

### ⚛️ Frontend (`/frontend`)
- **Next.js 16 (Turbopack) & React 19**: Framework moderno con renderizado SSR y Client Components.
- **Tailwind CSS & Framer Motion**: Diseño UI/UX moderno estilo Dashboard Dark Theme con efectos visuales interactivos (*TrueFocus* de React Bits).
- **Lucide React & Recharts**: Iconografía moderna y visualización gráfica de tendencias.

---

## 🚀 Funcionalidades Principales

1. **Detector de Oportunidades ML (`/oportunidades`)**:
   - Carga el **Top 50 de mejores oportunidades globales** o filtradas por barrio, ambientes, estado, rango de precio, baños, cochera y amenities.
   - Muestra el precio publicado vs. el valor estimado por Machine Learning, calculando el porcentaje de descuento y el margen de ganancia en USD.

2. **Índice USD/m² por Barrio (`/mercado`)**:
   - Ranking de medianas de precios por metro cuadrado en los 48 barrios oficiales de CABA, descartando distorsiones y publicaciones erróneas mediante IQR.

3. **Buscador Universal por Barrio (`/buscador`)**:
   - Filtro interactivo de propiedades en vivo sobre la base de datos de 92.000+ inmuebles.

4. **Calculadoras Financieras & Ajustes (`/calculadoras`)**:
   - **Simulador de Créditos UVA**: Cálculo de cuotas iniciales en UVA, ARS y USD con cotización oficial del dólar y valor UVA.
   - **Calculadora de Alquileres ICL / IPC**: Proyección de aumentos de contratos de alquiler según el Índice de Contratos de Locación (BCRA) o Inflación IPC (INDEC).

5. **Novedades en Tiempo Real**:
   - Extracción automatizada de noticias y análisis del sector inmobiliario.

---

## 🔒 Variables de Entorno

- **Backend (`backend/.env`)**: Contiene las credenciales `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` y `DB_NAME`.
- **Frontend (`frontend/.env.local`)**: Configuración de ambiente y proxies locales.
