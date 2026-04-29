"""
Página DéporHostelería — Cuenta de Explotación
================================================
Vista contable consolidada de las áreas de hostelería del estadio:
- KPIs globales (ingresos / costes / resultado / margen)
- P&L por área
- Evolución mensual
- Comparativa entre equipos (masculino / femenino / formativo)
- Top productos por unidades vendidas y por rotación
"""

import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

import dash
from dash import html, dcc, callback, Output, Input
import plotly.graph_objects as go
import pandas as pd

from database import (
    get_pre_cuenta_kpis_global,
    get_pre_cuenta_pl_area,
    get_pre_cuenta_costes_area,
    get_pre_cuenta_productos_partido,
    get_pre_cuenta_mensual_area,
    get_pre_rentabilidad_operativa,
    get_pre_costes_desglose,
)

dash.register_page(__name__, path="/hosteleria/cuenta-explotacion",
                   name="Cuenta de Explotación")


# =============================================================================
# HELPERS
# =============================================================================

ORDEN_MESES = ['AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
               'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO']

COLOR_INGRESOS = '#2ecc71'   # verde
COLOR_COSTES = '#e74c3c'     # rojo
COLOR_RESULTADO = '#1a3a5c'  # azul corporativo
COLOR_NEUTRO = '#95a5a6'

# Paleta para diferenciar áreas/equipos
COLORES_EQUIPO = {
    'masculino': '#1a3a5c',
    'femenino': '#c0392b',
    'formativo': '#f39c12',
    'desconocido': '#95a5a6',
}

# Paleta para categorías de costes
COLORES_COSTE = {
    'servicio_total': '#1a3a5c',  # azul corporativo (coste total servicio)
    'personal':       '#e74c3c',  # rojo (personal)
    'food':           '#f39c12',  # naranja (food)
    'beverage':       '#2c5282',  # azul medio (beverage)
    'varios':         '#95a5a6',  # gris (gastos varios)
    'mantenimiento':  '#9b59b6',  # morado
}

LABEL_COSTE = {
    'servicio_total': 'Servicio (Total)',
    'personal':       'Personal',
    'food':           'Food (Catering)',
    'beverage':       'Beverage',
    'varios':         'Gastos Varios',
    'mantenimiento':  'Mantenimiento',
}

# Paleta de colores para el listado de áreas (12 colores distintos)
PALETA_AREAS = [
    '#1a3a5c', '#c0392b', '#27ae60', '#f39c12', '#8e44ad', '#16a085',
    '#d35400', '#2c3e50', '#7f8c8d', '#e67e22', '#2980b9', '#c0392b',
]


def _color_rentabilidad(pct):
    """Devuelve color en función del nivel de rentabilidad operativa."""
    if pct is None or pd.isna(pct):
        return COLOR_NEUTRO
    if pct >= 50:
        return '#27ae60'   # verde fuerte
    if pct >= 30:
        return COLOR_INGRESOS
    if pct >= 15:
        return '#f39c12'   # naranja
    return COLOR_COSTES    # rojo


def fmt_eur(val, decimales=0):
    if val is None or pd.isna(val):
        return "—"
    txt = f"{float(val):,.{decimales}f}"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def fmt_pct(val, decimales=1):
    if val is None or pd.isna(val):
        return "—"
    return f"{float(val):.{decimales}f}".replace(".", ",") + " %"


def fmt_int(val):
    if val is None or pd.isna(val):
        return "—"
    return f"{int(val):,}".replace(",", ".")


# =============================================================================
# COMPONENTES DE LAYOUT
# =============================================================================

def kpi_card_simple(label, valor):
    """Tarjeta KPI estilo estándar de la plataforma (mismo formato que las
    secciones Entradas/Cesiones/Asistencia en modo "solo dato"): label arriba,
    valor en azul corporativo, sin comparativa."""
    return html.Div([
        html.Div(label, className="kpi-label-top",
                 style={"display": "flex", "alignItems": "center",
                         "justifyContent": "center", "gap": "5px"}),
        html.Div([
            html.Span(valor, className="kpi-value kpi-value-neutral"),
        ], style={"display": "flex", "alignItems": "baseline",
                   "justifyContent": "center", "gap": "5px"}),
    ], className="kpi-card")


def loading_component():
    return html.Div([
        html.Div(className="loading-spinner"),
        html.Div("Cargando datos...", className="loading-text"),
    ], className="loading-container")


# =============================================================================
# GRÁFICAS
# =============================================================================

def fig_pl_por_area(df_pl):
    """Barras horizontales agrupadas: ingresos, coste_total, resultado por área."""
    df = df_pl[df_pl['dimension'] == 'temporada'].copy()
    if df.empty:
        return go.Figure().update_layout(height=350,
            annotations=[{"text": "Sin datos", "showarrow": False}])

    df_g = df.groupby('area', as_index=False).agg(
        ingresos=('ingresos', 'sum'),
        coste_total=('coste_total', 'sum'),
        resultado=('resultado', 'sum'),
    )
    df_g = df_g.sort_values('resultado', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Ingresos', y=df_g['area'], x=df_g['ingresos'],
        orientation='h', marker_color=COLOR_INGRESOS,
        text=[fmt_eur(v) for v in df_g['ingresos']],
        textposition='outside', textfont=dict(size=9, color='#333'),
        hovertemplate='<b>%{y}</b><br>Ingresos: %{x:,.0f}€<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        name='Coste total', y=df_g['area'], x=df_g['coste_total'],
        orientation='h', marker_color=COLOR_COSTES,
        text=[fmt_eur(v) for v in df_g['coste_total']],
        textposition='outside', textfont=dict(size=9, color='#333'),
        hovertemplate='<b>%{y}</b><br>Coste: %{x:,.0f}€<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        name='Resultado', y=df_g['area'], x=df_g['resultado'],
        orientation='h', marker_color=COLOR_RESULTADO,
        text=[fmt_eur(v) for v in df_g['resultado']],
        textposition='outside', textfont=dict(size=9, color='#333'),
        hovertemplate='<b>%{y}</b><br>Resultado: %{x:,.0f}€<extra></extra>',
    ))
    fig.update_layout(
        barmode='group', height=max(400, len(df_g) * 75), bargap=0.25,
        margin=dict(t=10, b=20, l=120, r=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5,
                    xanchor="center", font=dict(family='Barlow Condensed', size=12)),
        xaxis=dict(showticklabels=False, zeroline=True),
        yaxis=dict(tickfont=dict(family='Barlow Condensed', size=11)),
        separators=',.',
    )
    return fig


def fig_evolucion_mensual(df_mensual):
    """Líneas: ingresos / coste / resultado totales por mes."""
    if df_mensual.empty:
        return go.Figure().update_layout(height=350,
            annotations=[{"text": "Sin datos mensuales", "showarrow": False}])

    df_g = df_mensual.groupby('mes', as_index=False).agg(
        ingresos=('ingresos', 'sum'),
        coste_total=('coste_total', 'sum'),
        resultado=('resultado', 'sum'),
    )
    # Orden cronológico
    df_g['orden'] = df_g['mes'].apply(
        lambda m: ORDEN_MESES.index(m) if m in ORDEN_MESES else 99)
    df_g = df_g.sort_values('orden')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_g['mes'], y=df_g['ingresos'],
        mode='lines+markers', name='Ingresos',
        line=dict(color=COLOR_INGRESOS, width=3), marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Ingresos: %{y:,.0f}€<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=df_g['mes'], y=df_g['coste_total'],
        mode='lines+markers', name='Coste total',
        line=dict(color=COLOR_COSTES, width=3), marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Coste: %{y:,.0f}€<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=df_g['mes'], y=df_g['resultado'],
        mode='lines+markers', name='Resultado',
        line=dict(color=COLOR_RESULTADO, width=3, dash='dot'), marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Resultado: %{y:,.0f}€<extra></extra>',
    ))
    fig.update_layout(
        height=380, margin=dict(t=20, b=40, l=60, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5,
                    xanchor="center", font=dict(family='Barlow Condensed', size=12)),
        xaxis=dict(tickfont=dict(family='Barlow Condensed', size=11)),
        yaxis=dict(tickfont=dict(family='Barlow Condensed', size=10),
                   gridcolor='rgba(0,0,0,0.06)'),
        plot_bgcolor='white', separators=',.',
    )
    return fig


def fig_comparativa_equipo(df_pl):
    """Barras agrupadas: ingresos / costes / resultado por equipo."""
    df = df_pl[df_pl['dimension'] == 'temporada'].copy()
    if df.empty:
        return go.Figure().update_layout(height=300,
            annotations=[{"text": "Sin datos", "showarrow": False}])
    df_g = df.groupby('equipo', as_index=False).agg(
        ingresos=('ingresos', 'sum'),
        coste_total=('coste_total', 'sum'),
        resultado=('resultado', 'sum'),
    )
    # Excluir 'desconocido' si tenemos suficientes con clasificación
    if (df_g['equipo'] != 'desconocido').sum() >= 2:
        df_g = df_g[df_g['equipo'] != 'desconocido']
    df_g['equipo_label'] = df_g['equipo'].str.upper()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Ingresos', x=df_g['equipo_label'], y=df_g['ingresos'],
        marker_color=COLOR_INGRESOS,
        text=[fmt_eur(v) for v in df_g['ingresos']],
        textposition='outside', textfont=dict(size=10, color='#333',
                                               family='Barlow Condensed', weight='bold'),
        hovertemplate='<b>%{x}</b><br>Ingresos: %{y:,.0f}€<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        name='Coste total', x=df_g['equipo_label'], y=df_g['coste_total'],
        marker_color=COLOR_COSTES,
        text=[fmt_eur(v) for v in df_g['coste_total']],
        textposition='outside', textfont=dict(size=10, color='#333',
                                               family='Barlow Condensed', weight='bold'),
        hovertemplate='<b>%{x}</b><br>Coste: %{y:,.0f}€<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        name='Resultado', x=df_g['equipo_label'], y=df_g['resultado'],
        marker_color=COLOR_RESULTADO,
        text=[fmt_eur(v) for v in df_g['resultado']],
        textposition='outside', textfont=dict(size=10, color='#333',
                                               family='Barlow Condensed', weight='bold'),
        hovertemplate='<b>%{x}</b><br>Resultado: %{y:,.0f}€<extra></extra>',
    ))
    fig.update_layout(
        barmode='group', height=380, bargap=0.3,
        margin=dict(t=20, b=40, l=60, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5,
                    xanchor="center", font=dict(family='Barlow Condensed', size=12)),
        xaxis=dict(tickfont=dict(family='Barlow Condensed', size=12)),
        yaxis=dict(showticklabels=False),
        plot_bgcolor='white', separators=',.',
    )
    return fig


def fig_top_productos(df_prod, top_n=10, ascending=False):
    """Barras horizontales: top N productos por unidades vendidas (acumulado temporada).
    ascending=False → top N MÁS vendidos. ascending=True → top N MENOS vendidos."""
    if df_prod is None or df_prod.empty:
        return go.Figure().update_layout(height=350,
            annotations=[{"text": "Sin datos", "showarrow": False}])

    # Agregar unidades por producto (sumando sobre dimension=partido para evitar
    # doble conteo con dimension=temporada que ya es el agregado)
    df = df_prod[df_prod['dimension'] == 'partido'].copy()
    if df.empty:
        df = df_prod[df_prod['dimension'] == 'temporada'].copy()

    df_g = df.groupby('producto', as_index=False).agg(uds=('unidades', 'sum'))
    df_g = df_g.sort_values('uds', ascending=ascending).head(top_n)
    df_g = df_g.sort_values('uds', ascending=True)  # Para que en horizontal el mayor esté arriba

    color = COLOR_RESULTADO if not ascending else COLOR_COSTES

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_g['uds'], y=df_g['producto'], orientation='h',
        marker_color=color,
        text=[fmt_int(v) + ' uds' for v in df_g['uds']],
        textposition='outside', textfont=dict(size=10, color='#333',
                                               family='Barlow Condensed', weight='bold'),
        hovertemplate='<b>%{y}</b><br>Unidades: %{x:,.0f}<extra></extra>',
    ))
    max_x = df_g['uds'].max() * 1.3 if len(df_g) > 0 else 100
    fig.update_layout(
        height=max(380, len(df_g) * 35), bargap=0.35,
        margin=dict(t=10, b=20, l=180, r=80),
        xaxis=dict(showticklabels=False, range=[0, max_x]),
        yaxis=dict(tickfont=dict(family='Barlow Condensed', size=11)),
        separators=',.',
    )
    return fig


def fig_ranking_rentabilidad(df_rent):
    """Barras horizontales: ranking de áreas por rentabilidad operativa de
    temporada (% margen). Color según nivel: rojo / naranja / verde."""
    if df_rent is None or df_rent.empty:
        return go.Figure().update_layout(height=350,
            annotations=[{"text": "Sin datos de rentabilidad", "showarrow": False}])

    df = df_rent[df_rent['dimension'] == 'temporada'].copy()
    if df.empty:
        return go.Figure().update_layout(height=350,
            annotations=[{"text": "Sin datos de temporada", "showarrow": False}])

    df = df.sort_values('rentabilidad_pct', ascending=True)
    colores = [_color_rentabilidad(v) for v in df['rentabilidad_pct']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['rentabilidad_pct'],
        y=df['area'],
        orientation='h',
        marker_color=colores,
        text=[fmt_pct(v) for v in df['rentabilidad_pct']],
        textposition='outside',
        textfont=dict(size=11, color='#333',
                       family='Barlow Condensed', weight='bold'),
        hovertemplate='<b>%{y}</b><br>Rentabilidad: %{x:.1f}%<extra></extra>',
    ))
    max_x = max(df['rentabilidad_pct'].max() * 1.18, 10) if len(df) > 0 else 100
    fig.update_layout(
        height=max(400, len(df) * 38), bargap=0.35,
        margin=dict(t=10, b=20, l=140, r=80),
        xaxis=dict(showticklabels=False, range=[0, max_x], zeroline=True),
        yaxis=dict(tickfont=dict(family='Barlow Condensed', size=11)),
        separators=',.',
    )
    return fig


def fig_evolucion_rentabilidad(df_rent):
    """Líneas multi-serie: rentabilidad mensual por área."""
    if df_rent is None or df_rent.empty:
        return go.Figure().update_layout(height=350,
            annotations=[{"text": "Sin datos", "showarrow": False}])

    df = df_rent[df_rent['dimension'] == 'mes'].copy()
    if df.empty:
        return go.Figure().update_layout(height=350,
            annotations=[{"text": "Sin datos mensuales", "showarrow": False}])

    df['orden'] = df['clave'].apply(
        lambda m: ORDEN_MESES.index(m) if m in ORDEN_MESES else 99)
    df = df.sort_values(['area', 'orden'])

    fig = go.Figure()
    areas = sorted(df['area'].unique())
    for i, area in enumerate(areas):
        sub = df[df['area'] == area]
        fig.add_trace(go.Scatter(
            x=sub['clave'], y=sub['rentabilidad_pct'],
            mode='lines+markers',
            name=area,
            line=dict(color=PALETA_AREAS[i % len(PALETA_AREAS)], width=2),
            marker=dict(size=6),
            hovertemplate=f'<b>{area}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>',
        ))
    fig.update_layout(
        height=400, margin=dict(t=20, b=40, l=60, r=20),
        legend=dict(orientation="v", yanchor="top", y=1, x=1.02,
                    xanchor="left", font=dict(family='Barlow Condensed', size=10)),
        xaxis=dict(tickfont=dict(family='Barlow Condensed', size=11)),
        yaxis=dict(tickfont=dict(family='Barlow Condensed', size=10),
                   ticksuffix='%', gridcolor='rgba(0,0,0,0.06)'),
        plot_bgcolor='white', separators=',.',
    )
    return fig


def fig_distribucion_costes(df_costes):
    """Donut chart: distribución de costes por categoría (temporada)."""
    if df_costes is None or df_costes.empty:
        return go.Figure().update_layout(height=380,
            annotations=[{"text": "Sin datos", "showarrow": False}])

    df = df_costes[df_costes['dimension'] == 'temporada'].copy()
    if df.empty:
        return go.Figure().update_layout(height=380,
            annotations=[{"text": "Sin datos de temporada", "showarrow": False}])

    df_g = df.groupby('categoria', as_index=False)['valor'].sum()
    df_g = df_g.sort_values('valor', ascending=False)

    labels = [LABEL_COSTE.get(c, c.title()) for c in df_g['categoria']]
    colores = [COLORES_COSTE.get(c, COLOR_NEUTRO) for c in df_g['categoria']]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=df_g['valor'],
        hole=0.5,
        marker=dict(colors=colores, line=dict(color='white', width=2)),
        textposition='outside',
        textinfo='label+percent',
        textfont=dict(family='Barlow Condensed', size=12),
        hovertemplate='<b>%{label}</b><br>%{value:,.0f}€ (%{percent})<extra></extra>',
    )])
    total = df_g['valor'].sum()
    fig.update_layout(
        height=380, margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
        annotations=[dict(
            text=f"<b>{fmt_eur(total)}</b><br><span style='font-size:0.8em;color:#666'>"
                 f"Costes Totales</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(family='Barlow Condensed', size=18, color='#1a3a5c'),
        )],
        separators=',.',
    )
    return fig


def fig_costes_por_area(df_costes):
    """Barras stacked horizontales: costes por área desglosados en categorías."""
    if df_costes is None or df_costes.empty:
        return go.Figure().update_layout(height=380,
            annotations=[{"text": "Sin datos", "showarrow": False}])

    df = df_costes[df_costes['dimension'] == 'temporada'].copy()
    if df.empty:
        return go.Figure().update_layout(height=380,
            annotations=[{"text": "Sin datos de temporada", "showarrow": False}])

    # Excluir 'servicio_total' del stack — es agregado, no es una categoría aditiva
    df_stack = df[df['categoria'] != 'servicio_total'].copy()
    if df_stack.empty:
        df_stack = df  # fallback

    pivot = df_stack.pivot_table(
        index='area', columns='categoria', values='valor',
        aggfunc='sum', fill_value=0
    )
    # Ordenar por total descendente
    pivot['_total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('_total', ascending=True).drop(columns='_total')

    fig = go.Figure()
    # Orden de las categorías para apilar (los componentes mayoritarios primero)
    orden_cat = ['personal', 'food', 'beverage', 'varios', 'mantenimiento']
    for cat in orden_cat:
        if cat not in pivot.columns:
            continue
        fig.add_trace(go.Bar(
            name=LABEL_COSTE.get(cat, cat),
            x=pivot[cat], y=pivot.index, orientation='h',
            marker_color=COLORES_COSTE.get(cat, COLOR_NEUTRO),
            hovertemplate=f'<b>%{{y}}</b><br>{LABEL_COSTE.get(cat, cat)}: '
                          '%{x:,.0f}€<extra></extra>',
        ))
    fig.update_layout(
        barmode='stack',
        height=max(400, len(pivot) * 38), bargap=0.3,
        margin=dict(t=10, b=20, l=140, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5,
                    xanchor="center", font=dict(family='Barlow Condensed', size=11)),
        xaxis=dict(tickfont=dict(family='Barlow Condensed', size=10),
                   gridcolor='rgba(0,0,0,0.06)'),
        yaxis=dict(tickfont=dict(family='Barlow Condensed', size=11)),
        plot_bgcolor='white', separators=',.',
    )
    return fig


# =============================================================================
# LAYOUT
# =============================================================================

layout = html.Div([
    dcc.Loading(
        id="loading-cuenta",
        type="default",
        fullscreen=False,
        children=html.Div(id="content-cuenta", children=loading_component()),
        custom_spinner=loading_component(),
    ),
])


# =============================================================================
# CALLBACK
# =============================================================================

@callback(
    Output("content-cuenta", "children"),
    Input("content-cuenta", "id"),
)
def render_cuenta(_):
    """Renderiza la página completa con todos los KPIs y gráficas."""
    try:
        df_kpis = get_pre_cuenta_kpis_global()
        df_pl = get_pre_cuenta_pl_area()
        df_mensual = get_pre_cuenta_mensual_area()
        df_prod = get_pre_cuenta_productos_partido()
        df_rent = get_pre_rentabilidad_operativa()
        df_costes_d = get_pre_costes_desglose()
    except Exception as e:
        return html.Div([
            html.Div("Error cargando datos de cuenta de explotación.",
                     style={"padding": "40px", "color": "#e74c3c",
                            "textAlign": "center", "fontWeight": 600}),
            html.Div(str(e), style={"padding": "10px", "color": "#999",
                                     "textAlign": "center", "fontSize": "0.85rem"}),
        ], className="page-content-container")

    if df_kpis.empty:
        return html.Div([
            html.Div("Aún no hay datos de cuenta de explotación. "
                     "Ejecuta el sync_data.py para poblar las tablas.",
                     style={"padding": "40px", "color": "#666",
                            "textAlign": "center", "fontStyle": "italic"}),
        ], className="page-content-container")

    # ----- KPIs globales (formato estándar de la plataforma) -----
    row_kpis = df_kpis.iloc[0]
    kpis_block = html.Div([
        kpi_card_simple("Ingresos Totales", fmt_eur(row_kpis['ingresos_totales'])),
        kpi_card_simple("Costes Totales", fmt_eur(row_kpis['costes_totales'])),
        kpi_card_simple("Resultado Operativo", fmt_eur(row_kpis['resultado_total'])),
        kpi_card_simple("Margen Global", fmt_pct(row_kpis['margen_pct_global'])),
    ], className="kpis-row")

    # ----- Gráficas (solo Ranking Rentabilidad + Distribución de Costes) -----
    fig_rank_rent = fig_ranking_rentabilidad(df_rent)
    fig_donut_costes = fig_distribucion_costes(df_costes_d)

    return html.Div([
        # Banda superior con título de la subsección
        html.Div("CUENTA DE EXPLOTACIÓN", className="banner-title"),

        # KPIs
        html.Div(kpis_block, className="kpis-container"),

        # Fila: Ranking Rentabilidad + Distribución Global de Costes
        html.Div([
            html.Div([
                html.H4("Ranking de Rentabilidad Operativa por Área"),
                dcc.Graph(figure=fig_rank_rent, config={'displayModeBar': False}),
                html.P("% de margen operativo (resultado / ingresos) de la temporada "
                        "completa. Verde ≥ 50%, naranja 30-50%, rojo < 30%.",
                       style={"fontSize": "0.72rem", "color": "#888",
                              "fontStyle": "italic", "textAlign": "center",
                              "marginTop": "4px"})
            ], className="graph-card"),
            html.Div([
                html.H4("Distribución Global de Costes"),
                dcc.Graph(figure=fig_donut_costes, config={'displayModeBar': False}),
                html.P("Reparto del coste total de la temporada por categoría: "
                        "personal, food (catering), beverage (bebidas) y gastos varios.",
                       style={"fontSize": "0.72rem", "color": "#888",
                              "fontStyle": "italic", "textAlign": "center",
                              "marginTop": "4px"})
            ], className="graph-card"),
        ], className="graphs-row"),

    ], className="page-content-container")
