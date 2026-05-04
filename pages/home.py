"""
Página de Inicio
=================
"""

import dash
from dash import html, dcc, callback, Output, Input
import pandas as pd
from database import (
    get_pre_entradas_partido, get_pre_hosteleria_partido,
    get_pre_deportiendas_kpis, get_museo_kpis,
    get_ficha_rivales_temp_actual,
    get_pre_cesiones_recaudacion,
)
from components import build_escudos_nav

dash.register_page(__name__, path="/", name="Inicio")

# Mapa de tarjetas → permiso requerido (0 = global)
# permiso: 1=Estadio, 2=Museo, 3=DéporTiendas, 4=DéporHosteleria
CARDS_CONFIG = [
    {"key": "estadio",      "permiso": 1, "title": "ESTADIO ABANCA-RIAZOR", "href": "/estadio/entradas"},
    {"key": "museo",        "permiso": 2, "title": "MUSEO RCD",              "href": "/museo"},
    {"key": "deportiendas", "permiso": 3, "title": "DÉPOR TIENDAS",          "href": "/deportiendas"},
    {"key": "hosteleria",   "permiso": 4, "title": "DÉPOR HOSTELERIA",       "href": "/hosteleria"},
]


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
                    html.Div(value_str,
                             className="home-card-value",
                             style={"color": value_color}),
                ]
            )
        ]
    )


def _load_home_data():
    """Carga datos para las tarjetas de inicio.

    `rec_estadio` agrupa la recaudación de la temporada actual de:
        - Entradas (`pre_entradas_partido.recaudacion`).
        - Cesiones vendidas (`pre_cesiones_recaudacion.rec_ces_vend`,
          que ya filtra por estado='V').
    De esta forma la tarjeta refleja el total de ingresos del estadio
    (entradas + mercado secundario), no solo entradas.
    """
    try:
        df_ent = get_pre_entradas_partido()
        rec_entradas = (df_ent[df_ent['temporada'] == 'actual']['recaudacion'].sum()
                        if not df_ent.empty else 0)
    except Exception:
        rec_entradas = 0

    try:
        df_ces = get_pre_cesiones_recaudacion()
        rec_cesiones = (df_ces[df_ces['temporada'] == 'actual']['rec_ces_vend'].sum()
                        if not df_ces.empty else 0)
    except Exception:
        rec_cesiones = 0

    rec_estadio = rec_entradas + rec_cesiones

    try:
        df_host = get_pre_hosteleria_partido()
        if not df_host.empty:
            rec_hosteleria = df_host[df_host['temporada'] == 'actual']['recaudacion_total'].sum()
        else:
            rec_hosteleria = 0
    except Exception:
        rec_hosteleria = 0

    try:
        df_dt = get_pre_deportiendas_kpis()
        if not df_dt.empty:
            rec_tiendas = df_dt.iloc[0]['recaudacion_total']
        else:
            rec_tiendas = 0
    except Exception:
        rec_tiendas = 0

    try:
        df_museo = get_museo_kpis()
        if not df_museo.empty:
            rec_museo = float(df_museo.iloc[0]['ingresos_netos'])
        else:
            rec_museo = 0
    except Exception:
        rec_museo = 0

    return rec_estadio, rec_hosteleria, rec_tiendas, rec_museo


def _build_card(cfg, data):
    """Construye una tarjeta según su config y datos precargados."""
    key = cfg["key"]
    if key == "estadio":
        return create_recaudacion_card(cfg["title"], f"{fmt(data['estadio'])}€",
                                       color="#18395c", is_active=True, href=cfg["href"])
    elif key == "museo":
        return create_recaudacion_card(cfg["title"], f"{fmt(data['museo'])}€",
                                       color="#18395c", is_active=True, href=cfg["href"])
    elif key == "deportiendas":
        return create_recaudacion_card(cfg["title"], f"{fmt(data['deportiendas'])}€",
                                       color="#18395c", is_active=True, href=cfg["href"])
    elif key == "hosteleria":
        return create_recaudacion_card(cfg["title"], f"{fmt(data['hosteleria'])}€",
                                       color="#18395c", is_active=True, href=cfg["href"])


layout = html.Div([
    # Banda azul corporativa "RECAUDACIÓN TOTAL" sobre las 4 tarjetas
    html.Div("RECAUDACIÓN TOTAL", className="banner-title"),
    html.Div(
        className="cards-container",
        id="home-cards-container",
        children=[]
    ),
    # Navegador de escudos (visible solo para admins)
    html.Div(id="home-escudos-nav", children=[]),
])


@callback(
    Output("home-cards-container", "children"),
    Output("home-escudos-nav", "children"),
    Input("session-store", "data"),
)
def update_home_cards(session):
    """Muestra solo las tarjetas a las que el usuario tiene acceso.
    El navegador de escudos (ficha post-partido) solo se muestra a admins."""
    rec_estadio, rec_hosteleria, rec_tiendas, rec_museo = _load_home_data()
    data = {"estadio": rec_estadio, "hosteleria": rec_hosteleria, "deportiendas": rec_tiendas, "museo": rec_museo}

    # Determinar permisos del usuario
    if session and session.get('authenticated'):
        permisos_raw = str(session.get('permisos', '0'))
        permisos_list = [p.strip() for p in permisos_raw.split(',')]
        is_global = '0' in permisos_list
    else:
        is_global = True
        permisos_list = ['0']

    # Filtrar tarjetas según permisos
    visible_cards = []
    for cfg in CARDS_CONFIG:
        if is_global or str(cfg["permiso"]) in permisos_list:
            visible_cards.append(_build_card(cfg, data))

    # Distribuir en filas de 2
    rows = []
    for i in range(0, len(visible_cards), 2):
        rows.append(html.Div(className="cards-row", children=visible_cards[i:i+2]))

    # Navegador de escudos: solo admins
    escudos_block = []
    if is_global:
        try:
            df_rivales = get_ficha_rivales_temp_actual()
            escudos_block = [build_escudos_nav(df_rivales, layout="grid",
                                               title="FICHA POST PARTIDO")]
        except Exception as e:
            print(f"Error cargando escudos: {e}")
            escudos_block = []

    return rows, escudos_block
