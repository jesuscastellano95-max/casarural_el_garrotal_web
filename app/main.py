# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 13:50:02 2026

@author: jesus
"""
import calendar
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from starlette.middleware.sessions import SessionMiddleware

from app.database import engine, crear_tablas
from app.models import Contacto, Reserva, PrecioNoche


app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="cambia-esta-clave-secreta"
)

crear_tablas()

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


def verificar_admin(request: Request):
    if not request.session.get("admin_logueado"):
        return RedirectResponse(url="/admin/login", status_code=303)
    return None


def obtener_fechas_ocupadas():
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

    return fechas_ocupadas


def generar_contexto_calendario(mes: int | None = None):
    hoy = date.today()
    year = hoy.year

    if mes is None:
        mes = hoy.month

    nombres_meses = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    meses_disponibles = list(range(hoy.month, 13))

    cal = calendar.Calendar(firstweekday=0)
    semanas = cal.monthdatescalendar(year, mes)

    fechas_ocupadas = obtener_fechas_ocupadas()

    return {
        "semanas": semanas,
        "fechas_ocupadas": fechas_ocupadas,
        "month": mes,
        "month_name": nombres_meses[mes],
        "year": year,
        "meses_disponibles": meses_disponibles,
        "mes_actual": mes,
        "hoy": hoy
    }


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
    nuevo_contacto = Contacto(
        nombre=nombre,
        email=email,
        telefono=telefono,
        mensaje=mensaje
    )

    with Session(engine) as session:
        session.add(nuevo_contacto)
        session.commit()

    return templates.TemplateResponse(
        request,
        "contacto.html",
        {
            "enviado": True,
            "nombre": nombre
        }
    )


@app.get("/reservas")
def reservas(request: Request, mes: int | None = None):
    contexto = generar_contexto_calendario(mes)

    return templates.TemplateResponse(
        request,
        "reservas.html",
        contexto
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

    contexto = generar_contexto_calendario(entrada.month)

    if salida <= entrada:
        contexto.update({
            "error": "La fecha de salida debe ser posterior a la fecha de entrada."
        })
        return templates.TemplateResponse(request, "reservas.html", contexto)

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
                contexto.update({
                    "error": "Para esta fecha ya existen reservas."
                })
                return templates.TemplateResponse(request, "reservas.html", contexto)

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

    contexto.update({
        "enviado": True,
        "nombre": nombre
    })

    return templates.TemplateResponse(
        request,
        "reservas.html",
        contexto
    )


@app.get("/calendario")
def calendario_reservas(request: Request, mes: int | None = None):
    contexto = generar_contexto_calendario(mes)

    return templates.TemplateResponse(
        request,
        "calendario.html",
        contexto
    )


@app.get("/admin/login")
def admin_login(request: Request):
    return templates.TemplateResponse(request, "admin_login.html")


@app.post("/admin/login")
def admin_login_post(
    request: Request,
    usuario: str = Form(...),
    password: str = Form(...)
):
    if usuario == "admin" and password == "admin123":
        request.session["admin_logueado"] = True
        return RedirectResponse(url="/admin", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin_login.html",
        {"error": "Usuario o contraseña incorrectos."}
    )


@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


@app.get("/admin")
def admin_dashboard(request: Request):
    redireccion = verificar_admin(request)
    if redireccion:
        return redireccion

    return templates.TemplateResponse(
        request,
        "admin_dashboard.html"
    )


@app.get("/admin/contactos")
def ver_contactos(request: Request):
    redireccion = verificar_admin(request)
    if redireccion:
        return redireccion

    with Session(engine) as session:
        contactos = session.exec(select(Contacto)).all()

    return templates.TemplateResponse(
        request,
        "admin_contactos.html",
        {
            "contactos": contactos
        }
    )


@app.get("/admin/reservas")
def ver_reservas(request: Request):
    redireccion = verificar_admin(request)
    if redireccion:
        return redireccion

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
def confirmar_reserva(request: Request, reserva_id: int):
    redireccion = verificar_admin(request)
    if redireccion:
        return redireccion

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
def cancelar_reserva(request: Request, reserva_id: int):
    redireccion = verificar_admin(request)
    if redireccion:
        return redireccion

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


@app.get("/admin/precios")
def admin_precios(request: Request):
    redireccion = verificar_admin(request)
    if redireccion:
        return redireccion

    with Session(engine) as session:
        precios = session.exec(
            select(PrecioNoche).order_by(PrecioNoche.fecha)
        ).all()

    return templates.TemplateResponse(
        request,
        "admin_precios.html",
        {
            "precios": precios
        }
    )


@app.post("/admin/precios")
def guardar_precio(
    request: Request,
    fecha: str = Form(...),
    precio: float = Form(...)
):
    redireccion = verificar_admin(request)
    if redireccion:
        return redireccion

    fecha_obj = date.fromisoformat(fecha)

    with Session(engine) as session:
        precio_existente = session.exec(
            select(PrecioNoche).where(PrecioNoche.fecha == fecha_obj)
        ).first()

        if precio_existente:
            precio_existente.precio = precio
            session.add(precio_existente)
        else:
            nuevo_precio = PrecioNoche(
                fecha=fecha_obj,
                precio=precio
            )
            session.add(nuevo_precio)

        session.commit()

    return RedirectResponse(
        url="/admin/precios",
        status_code=303
    )