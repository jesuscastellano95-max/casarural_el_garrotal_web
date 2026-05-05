# -*- coding: utf-8 -*-
"""
Created on Mon May  4 14:05:09 2026

@author: jesus
"""

from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import date


class Contacto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    telefono: Optional[str] = None
    mensaje: str

class Reserva(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    telefono: Optional[str] = None
    fecha_entrada: date
    fecha_salida: date
    numero_personas: int
    mensaje: Optional[str] = None
    estado: str = "pendiente"
