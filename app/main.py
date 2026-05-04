# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 13:50:02 2026

@author: jesus
"""
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlmodel import Session, select

from app.database import engine, crear_tablas
from app.models import Contacto


# Crear app
app = FastAPI()

# Crear tablas en la base de datos
crear_tablas()

# Rutas base
BASE_DIR = Path(__file__).resolve().parent

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Archivos estáticos (CSS, imágenes...)
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


# -------- RUTAS -------- #

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/alojamiento")
def alojamiento(request: Request):
    return templates.TemplateResponse(request, "alojamiento.html")


@app.get("/contacto")
def contacto(request: Request):
    return templates.TemplateResponse(request, "contacto.html")


@app.post("/contacto")
def enviar_contacto(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(""),
    mensaje: str = Form(...)
):
    # Crear objeto contacto
    nuevo_contacto = Contacto(
        nombre=nombre,
        email=email,
        telefono=telefono,
        mensaje=mensaje
    )

    # Guardar en base de datos
    with Session(engine) as session:
        session.add(nuevo_contacto)
        session.commit()

    # Respuesta al usuario
    return templates.TemplateResponse(
        request,
        "contacto.html",
        {
            "enviado": True,
            "nombre": nombre
        }
    )

@app.get("/admin/contactos")
def ver_contactos(request: Request):
    with Session(engine) as session:
        contactos = session.exec(select(Contacto)).all()

    return templates.TemplateResponse(
        request,
        "admin_contactos.html",
        {
            "contactos": contactos
        }
    )