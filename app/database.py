# -*- coding: utf-8 -*-
"""
Created on Mon May  4 13:44:25 2026

@author: jesus
"""

from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///database.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


def crear_tablas():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session