import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import calc, market, news

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="API REST modular para Inteligencia Inmobiliaria y Análisis Financiero en CABA"
)

# Candado de Seguridad 3: CORS Restringido
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar Routers Modulares
app.include_router(calc.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(news.router, prefix="/api")

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "Bienvenido a la API REST de Departamentos CABA",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
