# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 13:50:02 2026

@author: jesus
"""
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

import calendar
from datetime import date, timedelta

from sqlmodel import Session, select

from app.database import engine, crear_tablas
from app.models import Contacto, Reserva


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

#Función reutilizable calendario#

def generar_calendarios_disponibilidad():
    hoy = date.today()
    year = hoy.year

    with Session(engine) as session:
        reservas_confirmadas = session.exec(
            select(Reserva).where(Reserva.estado == "confirmada")
        ).all()

    fechas_ocupadas = set()

    for reserva in reservas_confirmadas:
        dia = reserva.fecha_entrada

        while dia < reserva.fecha_salida:
            fechas_ocupadas.add(dia.isoformat())
            dia += timedelta(days=1)

    nombres_meses = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    cal = calendar.Calendar(firstweekday=0)
    calendarios = []

    for month in range(hoy.month, 13):
        semanas = cal.monthdatescalendar(year, month)

        calendarios.append({
            "month": month,
            "month_name": nombres_meses[month],
            "year": year,
            "semanas": semanas
        })

    return calendarios, fechas_ocupadas, hoy

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

@app.get("/reservas")
def reservas(request: Request):
    calendarios, fechas_ocupadas, hoy = generar_calendarios_disponibilidad()

    return templates.TemplateResponse(
        request,
        "reservas.html",
        {
            "calendarios": calendarios,
            "fechas_ocupadas": fechas_ocupadas,
            "hoy": hoy
        }
    )


@app.post("/reservas")
def enviar_reserva(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    telefono: str = Form(""),
    fecha_entrada: str = Form(...),
    fecha_salida: str = Form(...),
    numero_personas: int = Form(...),
    mensaje: str = Form("")
):
    entrada = date.fromisoformat(fecha_entrada)
    salida = date.fromisoformat(fecha_salida)

    if salida <= entrada:
        return templates.TemplateResponse(
            request,
            "reservas.html",
            {
                "error": "La fecha de salida debe ser posterior a la fecha de entrada."
            }
        )

    with Session(engine) as session:
        reservas_confirmadas = session.exec(
            select(Reserva).where(Reserva.estado == "confirmada")
        ).all()

        for reserva in reservas_confirmadas:
            hay_solapamiento = (
                entrada < reserva.fecha_salida
                and salida > reserva.fecha_entrada
            )

            if hay_solapamiento:
                return templates.TemplateResponse(
                    request,
                    "reservas.html",
                    {
                        "error": "Para esta fecha ya existen reservas."
                    }
                )

        nueva_reserva = Reserva(
            nombre=nombre,
            email=email,
            telefono=telefono,
            fecha_entrada=entrada,
            fecha_salida=salida,
            numero_personas=numero_personas,
            mensaje=mensaje,
            estado="pendiente"
        )

        session.add(nueva_reserva)
        session.commit()

    return templates.TemplateResponse(
        request,
        "reservas.html",
        {
            "enviado": True,
            "nombre": nombre
        }
    )


@app.get("/admin/reservas")
def ver_reservas(request: Request):
    with Session(engine) as session:
        reservas = session.exec(select(Reserva)).all()

    return templates.TemplateResponse(
        request,
        "admin_reservas.html",
        {
            "reservas": reservas
        }
    )

@app.post("/admin/reservas/{reserva_id}/confirmar")
def confirmar_reserva(reserva_id: int):
    with Session(engine) as session:
        reserva = session.get(Reserva, reserva_id)

        if reserva:
            reserva.estado = "confirmada"
            session.add(reserva)
            session.commit()

    return RedirectResponse(
        url="/admin/reservas",
        status_code=303
    )


@app.post("/admin/reservas/{reserva_id}/cancelar")
def cancelar_reserva(reserva_id: int):
    with Session(engine) as session:
        reserva = session.get(Reserva, reserva_id)

        if reserva:
            reserva.estado = "cancelada"
            session.add(reserva)
            session.commit()

    return RedirectResponse(
        url="/admin/reservas",
        status_code=303
    )

@app.get("/calendario")
def calendario_reservas(request: Request):
    calendarios, fechas_ocupadas, hoy = generar_calendarios_disponibilidad()

    return templates.TemplateResponse(
        request,
        "calendario.html",
        {
            "calendarios": calendarios,
            "fechas_ocupadas": fechas_ocupadas,
            "hoy": hoy
        }
    )