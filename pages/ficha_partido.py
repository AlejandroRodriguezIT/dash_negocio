"""
Ficha Post-Partido
==================
Vista por partido con los KPIs más relevantes de cada sección de negocio.
Ruta dinámica: /ficha-partido/<id_partido>
Acceso: únicamente usuarios con permiso '0' (admin).
"""

import dash
from dash import html, dcc, callback, Output, Input
import pandas as pd
from datetime import datetime

from database import get_ficha_partido, get_ficha_rivales_temp_actual
from components import build_escudos_nav, get_escudo_path

dash.register_page(
    __name__,
    path_template="/ficha-partido/<id_partido>",
    name="Ficha Post-Partido",
)


# =============================================================================
# HELPERS DE FORMATO
# =============================================================================

DIAS_ES = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado',
    'Sunday': 'Domingo',
}


def _fmt_int(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{int(v):,}".replace(",", ".")


def _fmt_eur(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{float(v):,.0f}€".replace(",", ".")


def _fmt_eur2(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{float(v):,.2f}€".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{float(v):.1f}%".replace(".", ",")


def _fmt_edad(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{float(v):.1f} años".replace(".", ",")


def _resultado_class(result_str):
    """Devuelve ('W'|'L'|'D'|'') según el resultado."""
    if not result_str or pd.isna(result_str):
        return ""
    try:
        parts = str(result_str).split('-')
        home, away = int(parts[0]), int(parts[1])
        if home > away:
            return "win"
        if home < away:
            return "loss"
        return "draw"
    except Exception:
        return ""


def _fecha_larga(schedule):
    """Devuelve 'Domingo, 18:30 · 23/04/2026'."""
    if pd.isna(schedule):
        return ""
    dt = pd.to_datetime(schedule)
    dia = DIAS_ES.get(dt.strftime('%A'), dt.strftime('%A'))
    return f"{dia}, {dt.strftime('%H:%M')} · {dt.strftime('%d/%m/%Y')}"


# =============================================================================
# COMPONENTES DE LA FICHA
# =============================================================================

def _kpi(label, value):
    return html.Div([
        html.Div(label, className="ficha-kpi-label"),
        html.Div(value, className="ficha-kpi-value"),
    ], className="ficha-kpi")


def _kpi_muted(label, value):
    return html.Div([
        html.Div(label, className="ficha-kpi-label"),
        html.Div(value, className="ficha-kpi-value ficha-kpi-value--muted"),
    ], className="ficha-kpi")


def _columna(titulo_vertical, children):
    """Construye una columna-vertical: cabecera azul + cuerpo con KPIs apilados."""
    return html.Div([
        html.Div(titulo_vertical, className="ficha-columna-header"),
        html.Div(children, className="ficha-columna-body"),
    ], className="ficha-columna")


def _build_ficha(row, df_rivales):
    """Construye el layout completo de la ficha para una fila de pre_ficha_partido.

    Layout:
        +------------+-----------+-----------------+
        | ASISTENCIA | CESIONES  | DÉPOR HOSTELERÍA|
        +------------+-----------+-----------------+
        |        IDENTIDAD DEL PARTIDO              |
        +------------+-----------+-----------------+
        | ENTRADAS   | MUSEO RCD | DÉPOR TIENDAS   |
        +------------+-----------+-----------------+
    """
    rival = row['t2_name']
    escudo = get_escudo_path(rival)

    # ---- Banda central IDENTIDAD (horizontal: escudo | info | resultado) ----
    res = row.get('result') or ""
    res_cls = _resultado_class(res)
    cls_map = {
        'win':  "ficha-header-resultado ficha-header-resultado--win",
        'loss': "ficha-header-resultado ficha-header-resultado--loss",
        'draw': "ficha-header-resultado ficha-header-resultado--draw",
    }
    resultado_div = html.Div(
        res if res else "—",
        className=cls_map.get(res_cls, "ficha-header-resultado"),
    )

    col_identidad = html.Div([
        html.Img(src=escudo, className="ficha-header-escudo") if escudo else html.Div(),
        html.Div([
            html.H2(rival.upper(), className="ficha-header-rival"),
            html.Div(_fecha_larga(row['schedule']), className="ficha-header-fecha"),
            resultado_div,
        ], className="ficha-identidad-info"),
    ], className="ficha-columna-identidad")

    # ---- Fila superior (más tarjetas) ----
    if not pd.isna(row.get('male_pct')) and not pd.isna(row.get('female_pct')):
        sexo_txt = f"{_fmt_pct(row['male_pct'])} H · {_fmt_pct(row['female_pct'])} M"
    else:
        sexo_txt = "—"

    col_asistencia = _columna("ASISTENCIA", [
        _kpi("ESPECTADORES TOTALES", _fmt_int(row.get('total_espectadores'))),
        _kpi("ABONADOS ASISTENTES", _fmt_int(row.get('abonados_asistentes'))),
        _kpi("% ABONADOS ASISTENTES", _fmt_pct(row.get('abonados_pct'))),
        _kpi("SEXO ABONADOS", sexo_txt),
        _kpi("EDAD PROMEDIO", _fmt_edad(row.get('edad_promedio'))),
    ])

    col_cesiones = _columna("CESIONES", [
        _kpi("RECAUDACIÓN", _fmt_eur(row.get('cesiones_recaudacion'))),
        _kpi("CESIONES GENERADAS", _fmt_int(row.get('cesiones_generadas'))),
        _kpi("CESIONES VENDIDAS", _fmt_int(row.get('cesiones_vendidas'))),
        _kpi("% CESIONES VENDIDAS", _fmt_pct(row.get('cesiones_pct_vendidas'))),
    ])

    col_host = _columna("DÉPOR HOSTELERÍA", [
        _kpi("RECAUDACIÓN", _fmt_eur(row.get('host_recaudacion'))),
        _kpi("TICKET MEDIO", _fmt_eur2(row.get('host_ticket_medio'))),
        _kpi("Nº DE PEDIDOS", _fmt_int(row.get('host_n_pedidos'))),
        _kpi("INGRESO POR ASISTENTE", _fmt_eur2(row.get('host_ingreso_por_asistente'))),
    ])

    # ---- Fila inferior (menos tarjetas) ----
    col_entradas = _columna("ENTRADAS", [
        _kpi("RECAUDACIÓN", _fmt_eur(row.get('entradas_recaudacion'))),
        _kpi("Nº ENTRADAS VENDIDAS", _fmt_int(row.get('entradas_vendidas'))),
        _kpi("% ENTRADAS VENDIDAS", _fmt_pct(row.get('entradas_pct'))),
    ])

    if pd.isna(row.get('museo_entradas')) and pd.isna(row.get('museo_ingresos')):
        col_museo = _columna("MUSEO RCD", [
            _kpi_muted("ESTADO", "Museo aún no abierto en esta fecha"),
        ])
    else:
        col_museo = _columna("MUSEO RCD", [
            _kpi("ENTRADAS VENDIDAS", _fmt_int(row.get('museo_entradas'))),
            _kpi("INGRESOS TOTALES", _fmt_eur(row.get('museo_ingresos'))),
        ])

    col_tiendas = _columna("DÉPOR TIENDAS", [
        _kpi("VENTAS MATCHDAY (RIAZOR)", _fmt_eur(row.get('tiendas_ventas_matchday'))),
    ])

    # Orden en DOM: fila superior → identidad (banda) → fila inferior
    grid = html.Div([
        col_asistencia, col_cesiones, col_host,
        col_identidad,
        col_entradas, col_museo, col_tiendas,
    ], className="ficha-grid")

    escudos_nav = build_escudos_nav(df_rivales, layout="ficha", active_id=row['id_partido'])

    return html.Div([
        escudos_nav,
        grid,
    ], className="page-content-container")


def _layout_no_disponible(msg="Ficha no disponible para este partido."):
    return html.Div([
        html.Div(msg, style={"padding": "40px", "textAlign": "center",
                             "color": "#666", "fontWeight": 600}),
        dcc.Link("Volver al inicio", href="/",
                 style={"display": "block", "textAlign": "center",
                        "color": "#1a3a5c", "fontWeight": 600}),
    ], className="page-content-container")


def _layout_no_autorizado():
    return html.Div([
        html.Div("Acceso restringido. Esta sección solo está disponible para administradores.",
                 style={"padding": "40px", "textAlign": "center",
                        "color": "#e74c3c", "fontWeight": 600}),
        dcc.Link("Volver al inicio", href="/",
                 style={"display": "block", "textAlign": "center",
                        "color": "#1a3a5c", "fontWeight": 600}),
    ], className="page-content-container")


# =============================================================================
# LAYOUT (función — recibe parámetros de la ruta dinámica)
# =============================================================================

def layout(id_partido=None, **kwargs):
    """Dash invoca esta función con los parámetros de la ruta dinámica."""
    return html.Div([
        # Marcador oculto con el id del partido; el callback real lo lee
        # desde dcc.Location para poder validar sesión/permiso.
        dcc.Store(id="ficha-id-partido", data={"id": id_partido}),
        html.Div(id="ficha-content", children=[]),
    ])


# =============================================================================
# CALLBACK
# =============================================================================

@callback(
    Output("ficha-content", "children"),
    Input("ficha-id-partido", "data"),
    Input("session-store", "data"),
)
def render_ficha(store_data, session):
    # Validar sesión y permiso admin
    if not session or not session.get('authenticated'):
        return _layout_no_autorizado()
    permisos_raw = str(session.get('permisos', ''))
    permisos_list = [p.strip() for p in permisos_raw.split(',')]
    if '0' not in permisos_list:
        return _layout_no_autorizado()

    # Validar id
    id_partido = (store_data or {}).get('id')
    try:
        id_partido_int = int(id_partido)
    except (TypeError, ValueError):
        return _layout_no_disponible("ID de partido no válido.")

    # Cargar datos
    try:
        df = get_ficha_partido(id_partido_int)
    except Exception as e:
        return _layout_no_disponible(f"Error cargando ficha: {e}")

    if df.empty:
        return _layout_no_disponible()

    try:
        df_rivales = get_ficha_rivales_temp_actual()
    except Exception:
        df_rivales = pd.DataFrame()

    return _build_ficha(df.iloc[0], df_rivales)
