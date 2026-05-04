# -*- coding: utf-8 -*-
"""
Created on Mon May  4 14:05:09 2026

@author: jesus
"""

from typing import Optional
from sqlmodel import SQLModel, Field


class Contacto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    telefono: Optional[str] = None
    mensaje: str