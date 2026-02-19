"""
Página de Inicio
=================
"""

import dash
from dash import html, dcc, callback, Output, Input
import pandas as pd
from database import (
    get_pre_entradas_partido, get_pre_hosteleria_partido
)

dash.register_page(__name__, path="/", name="Inicio")


def fmt(val):
    """Formatea número con puntos como separador de miles."""
    return f"{val:,.0f}".replace(",", ".")


def create_recaudacion_card(title, value_str, color="#18395c", is_active=True, href="#"):
    """Crea una tarjeta de recaudación para la página de inicio."""
    value_color = color if is_active else "#999"
    return dcc.Link(
        href=href,
        className="home-card-link",
        children=[
            html.Div(
                className="home-card",
                children=[
                    html.H3(title, className="home-card-title"),
                    html.Div("RECAUDACIÓN TOTAL",
                             className="home-card-subtitle"),
                    html.Div(value_str,
                             className="home-card-value",
                             style={"color": value_color}),
                ]
            )
        ]
    )


def _load_home_data():
    """Carga datos para las tarjetas de inicio."""
    try:
        df_ent = get_pre_entradas_partido()
        if not df_ent.empty:
            rec_estadio = df_ent[df_ent['temporada'] == 'actual']['recaudacion'].sum()
        else:
            rec_estadio = 0
    except Exception:
        rec_estadio = 0

    try:
        df_host = get_pre_hosteleria_partido()
        if not df_host.empty:
            rec_hosteleria = df_host[df_host['temporada'] == 'actual']['recaudacion_total'].sum()
        else:
            rec_hosteleria = 0
    except Exception:
        rec_hosteleria = 0

    return rec_estadio, rec_hosteleria


rec_estadio, rec_hosteleria = _load_home_data()

layout = html.Div(
    className="cards-container",
    children=[
        # Fila 1
        html.Div(
            className="cards-row",
            children=[
                create_recaudacion_card(
                    "ESTADIO ABANCA-RIAZOR",
                    f"{fmt(rec_estadio)}€",
                    color="#18395c",
                    is_active=True,
                    href="/estadio/entradas",
                ),
                create_recaudacion_card(
                    "MUSEO RCD",
                    "EN DESARROLLO",
                    color="#999",
                    is_active=False,
                    href="/museo",
                ),
            ]
        ),
        # Fila 2
        html.Div(
            className="cards-row",
            children=[
                create_recaudacion_card(
                    "DÉPOR TIENDAS",
                    "EN DESARROLLO",
                    color="#999",
                    is_active=False,
                    href="/deportiendas",
                ),
                create_recaudacion_card(
                    "DÉPOR HOSTELERIA",
                    f"{fmt(rec_hosteleria)}€",
                    color="#18395c",
                    is_active=True,
                    href="/hosteleria",
                ),
            ]
        ),
    ]
)
