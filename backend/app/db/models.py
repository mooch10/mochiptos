from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Departamento(Base):
    __tablename__ = 'departamentos'

    id_publicacion = Column(String(255), primary_key=True)
    portal = Column(String(50), nullable=False)
    titulo_aviso = Column(String(500), nullable=True)
    barrio = Column(String(100), nullable=True)
    direccion = Column(String(255), nullable=True)
    ambientes = Column(Integer, nullable=True)
    habitaciones = Column(Integer, nullable=True)
    banos = Column(Integer, nullable=True)
    estado_propiedad = Column(String(100), nullable=True)
    precio_usd = Column(Float, nullable=True)
    m2_totales = Column(Float, nullable=True)
    m2_cubiertos = Column(Float, nullable=True)
    precio_m2 = Column(Float, nullable=True)
    expensas = Column(Float, default=0.0, nullable=True)
    antiguedad = Column(Integer, default=0, nullable=True)
    disposicion = Column(String(50), nullable=True)
    descripcion_cruda = Column(Text, nullable=True)
    tiene_cochera = Column(Boolean, default=False, nullable=True)
    tiene_amenities = Column(Boolean, default=False, nullable=True)
    desarrolladora = Column(String(255), nullable=True)
    url_publicacion = Column(String(1000), nullable=True)
    fecha_primera_extraccion = Column(DateTime, default=datetime.now)
    fecha_ultima_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
