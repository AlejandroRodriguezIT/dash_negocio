"""
Página DeporHosteleria
==========================================
Análisis de ventas de food & beverage por partido
Con filtro por hora de inicio del partido.
"""

import dash
from dash import html, dcc, callback, Output, Input, State, ctx, no_update
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from database import (
    get_pre_hosteleria_partido, get_pre_hosteleria_producto,
    get_pre_hosteleria_cantina, get_pre_hosteleria_metodo_pago,
    get_pre_hosteleria_producto_cantina,
    get_pre_asistencia_partido,
)

dash.register_page(__name__, path="/hosteleria", name="DeporHosteleria")

# Traducción días de la semana
DIAS_ES = {
    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo',
}

# Definición de franjas horarias
FRANJAS = {
    'MEDIODIA': {'horas': ['14:00', '16:15'], 'label': 'MEDIODÍA', 'subtitle': '14:00 - 16:15'},
    'TARDE':    {'horas': ['17:00', '18:30', '19:00'], 'label': 'TARDE', 'subtitle': '17:00 - 19:00'},
    'NOCHE':    {'horas': ['20:30', '21:00'], 'label': 'NOCHE', 'subtitle': '20:30 - 21:00'},
}

# Clasificación de productos: bebidas vs comestibles
# Todo lo que no sea bebida ni excluido se considera comestible
BEBIDAS_KEYWORDS = [
    'agua', 'aquarius', 'botella', 'café', 'caña', 'cerveza', 'clara',
    'coca', 'colacao', 'copa vino', 'descafeinado', 'estrella tostada',
    'fanta', 'gintonic', 'nestea', 'ron', 'tónica', 'zumo',
]
EXCLUIDOS_KEYWORDS = ['vaso depor', 'bufanda']

# Agrupación de nombres de producto duplicados
PRODUCT_NAME_MAP = {
    'Agua Cabreiroá': 'Agua Cabreiroa',
    'Aquarius Limón': 'Aquarius',
    'Café Cortado': 'Café',
    'Café con leche': 'Café',
    'Café de Pota': 'Café',
    'Coca-Cola': 'Coca Cola',
    'Coca-Cola Zero': 'Coca Cola Zero',
    'Cerveza tostada 0\'0': 'Tostada 0\'0',
    'Estrella Tostada 0\'0': 'Tostada 0\'0',
}


def normalizar_producto(nombre):
    """Normaliza el nombre de un producto agrupando duplicados."""
    return PRODUCT_NAME_MAP.get(nombre, nombre)


def clasificar_producto(nombre):
    """Clasifica un producto como 'bebida', 'comestible' o 'excluido'."""
    nl = nombre.lower()
    if any(kw in nl for kw in EXCLUIDOS_KEYWORDS):
        return 'excluido'
    if any(kw in nl for kw in BEBIDAS_KEYWORDS):
        return 'bebida'
    return 'comestible'


# Mapeo de nombres de equipos a archivos de escudos
ESCUDOS_MAP = {
    'Albacete': 'Albacete BP.png',
    'Albacete BP': 'Albacete BP.png',
    'Atlético de Madrid': 'Atletico de Madrid.png',
    'Atletico de Madrid': 'Atletico de Madrid.png',
    'Burgos': 'Burgos CF.png',
    'Burgos CF': 'Burgos CF.png',
    'Castellón': 'CD Castellón.png',
    'CD Castellón': 'CD Castellón.png',
    'Leganés': 'CD Leganés.png',
    'CD Leganés': 'CD Leganés.png',
    'Mirandés': 'CD Mirandés.png',
    'CD Mirandés': 'CD Mirandés.png',
    'Ceuta': 'Ceuta.png',
    'AD Ceuta': 'Ceuta.png',
    'AD Ceuta FC': 'Ceuta.png',
    'Cultural Leonesa': 'Cultural.png',
    'Cultural': 'Cultural.png',
    'Cádiz': 'Cádiz CF.png',
    'Cádiz CF': 'Cádiz CF.png',
    'Córdoba': 'Córdoba CF.png',
    'Córdoba CF': 'Córdoba CF.png',
    'Andorra': 'FC Andorra.png',
    'FC Andorra': 'FC Andorra.png',
    'Granada': 'Granada CF.png',
    'Granada CF': 'Granada CF.png',
    'Mallorca': 'Mallorca.png',
    'RCD Mallorca': 'Mallorca.png',
    'Málaga': 'Málaga CF.png',
    'Málaga CF': 'Málaga CF.png',
    'Deportivo': 'RC Deportivo.png',
    'RC Deportivo': 'RC Deportivo.png',
    'Deportivo de La Coruña': 'RC Deportivo.png',
    'Racing': 'Real Racing Club.png',
    'Racing de Santander': 'Real Racing Club.png',
    'Real Racing Club': 'Real Racing Club.png',
    'Real Sociedad B': 'Real Sociedad B.png',
    'Real Sociedad II': 'Real Sociedad B.png',
    'Sporting': 'Real Sporting.png',
    'Real Sporting': 'Real Sporting.png',
    'Sporting de Gijón': 'Real Sporting.png',
    'Valladolid': 'Real Valladolid CF.png',
    'Real Valladolid': 'Real Valladolid CF.png',
    'Real Valladolid CF': 'Real Valladolid CF.png',
    'Zaragoza': 'Real Zaragoza.png',
    'Real Zaragoza': 'Real Zaragoza.png',
    'Eibar': 'SD Eibar.png',
    'SD Eibar': 'SD Eibar.png',
    'Huesca': 'SD Huesca.png',
    'SD Huesca': 'SD Huesca.png',
    'Almería': 'UD Almería.png',
    'UD Almería': 'UD Almería.png',
    'Las Palmas': 'UD Las Palmas.png',
    'UD Las Palmas': 'UD Las Palmas.png',
}


def get_escudo_path(team_name):
    """Obtiene la ruta del escudo para un equipo."""
    escudo_file = ESCUDOS_MAP.get(team_name)
    if escudo_file:
        return f"/assets/Escudos/{escudo_file}"
    return None


def format_with_dots(val):
    """Formatea número con puntos como separador de miles."""
    return f"{val:,.0f}".replace(",", ".")


def fmt(val):
    """Alias corto de format_with_dots."""
    return f"{val:,.0f}".replace(",", ".")


def get_result_color(result_str):
    """Devuelve color según resultado del partido (perspectiva local)."""
    try:
        parts = result_str.split('-')
        home, away = int(parts[0]), int(parts[1])
        if home > away:
            return '#2ecc71'
        elif home < away:
            return '#e74c3c'
        else:
            return '#f39c12'
    except:
        return '#95a5a6'


def create_escudos_with_result(rivales, results, y_pos=-0.09, sizex=0.55, sizey=0.10):
    """Crea imágenes de escudos con círculos coloreados según resultado."""
    images = []
    shapes = []
    for i, (rival, result) in enumerate(zip(rivales, results)):
        color = get_result_color(result)
        shapes.append(dict(
            type="circle",
            xref="x", yref="paper",
            x0=i - 0.30, x1=i + 0.30,
            y0=y_pos - 0.06, y1=y_pos + 0.06,
            line=dict(color=color, width=2.5),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        ))
        escudo_path = get_escudo_path(rival)
        if escudo_path:
            images.append(dict(
                source=escudo_path,
                xref="x", yref="paper",
                x=i, y=y_pos,
                sizex=sizex, sizey=sizey,
                xanchor="center", yanchor="middle"
            ))
    return images, shapes


def _kpi_tooltip(text):
    """Genera el icono (?) con tooltip para tarjetas KPI."""
    if not text:
        return None
    return html.Div([
        html.Span("?", className="kpi-tooltip-icon"),
        html.Div(text, className="kpi-tooltip-box"),
    ], className="kpi-tooltip-wrapper")


def create_kpi_card(valor_actual, valor_anterior, label, formato="numero", tooltip=None):
    """Crea una tarjeta KPI con comparativa y % de diferencia.

    Si valor_anterior es None, muestra sólo el valor actual sin comparativa
    (modo análisis individual).
    """
    label_children = [label]
    if tooltip:
        label_children.append(_kpi_tooltip(tooltip))
    label_div = html.Div(label_children, className="kpi-label-top",
                         style={"display": "flex", "alignItems": "center",
                                "justifyContent": "center", "gap": "5px"})

    if formato == "euros":
        texto_actual = f"{fmt(valor_actual)}€"
    else:
        texto_actual = fmt(valor_actual)

    if valor_anterior is None:
        return html.Div([
            label_div,
            html.Div(
                html.Span(texto_actual, className="kpi-value kpi-value-neutral"),
                style={"display": "flex", "alignItems": "baseline", "justifyContent": "center"},
            ),
            html.Div("Selección individual", className="kpi-previous"),
        ], className="kpi-card")

    if formato == "euros":
        texto_anterior = f"{fmt(valor_anterior)}€"
    else:
        texto_anterior = fmt(valor_anterior)

    if valor_anterior > 0:
        pct_diff = ((valor_actual - valor_anterior) / valor_anterior) * 100
        if pct_diff >= 0:
            pct_text = f"+{pct_diff:.1f}%"
            color_class = "kpi-value-positive"
        else:
            pct_text = f"{pct_diff:.1f}%"
            color_class = "kpi-value-negative"
    else:
        pct_text = "N/A"
        color_class = "kpi-value-positive" if valor_actual >= valor_anterior else "kpi-value-negative"

    return html.Div([
        label_div,
        html.Div([
            html.Span(texto_actual, className=f"kpi-value {color_class}"),
            html.Span(f" ({pct_text})", className=f"kpi-pct-diff {color_class}")
        ], style={"display": "flex", "alignItems": "baseline", "justifyContent": "center", "gap": "5px"}),
        html.Div(f"Temp. 24/25: {texto_anterior}", className="kpi-previous"),
    ], className="kpi-card")


def create_kpi_card_hora(valor, label, media_global, formato="numero", tooltip=None):
    """KPI card para vista por hora, comparando contra media global."""
    label_children = [label]
    if tooltip:
        label_children.append(_kpi_tooltip(tooltip))
    label_div = html.Div(label_children, className="kpi-label-top",
                         style={"display": "flex", "alignItems": "center",
                                "justifyContent": "center", "gap": "5px"})

    if formato == "euros":
        texto = f"{fmt(valor)}€"
    else:
        texto = fmt(valor)

    if media_global > 0:
        pct_diff = ((valor - media_global) / media_global) * 100
        if pct_diff >= 0:
            pct_text = f"+{pct_diff:.1f}% vs media"
            color_class = "kpi-value-positive"
        else:
            pct_text = f"{pct_diff:.1f}% vs media"
            color_class = "kpi-value-negative"
    else:
        pct_text = "N/A"
        color_class = "kpi-value-positive"

    return html.Div([
        label_div,
        html.Div([
            html.Span(texto, className=f"kpi-value {color_class}"),
            html.Span(f" ({pct_text})", className=f"kpi-pct-diff {color_class}")
        ], style={"display": "flex", "alignItems": "baseline", "justifyContent": "center", "gap": "5px"}),
        html.Div(f"Media global: {fmt(media_global)}{'€' if formato == 'euros' else ''}", className="kpi-previous"),
    ], className="kpi-card")


# Componente de loading
def loading_component():
    return html.Div([
        html.Div(className="loading-spinner"),
        html.Div("Cargando datos...", className="loading-text")
    ], className="loading-container")


def create_section_header():
    """Crea el header con título y botones de franja horaria."""
    tabs = [
        {"id": "btn-franja-GLOBAL",    "label": "GLOBAL",    "subtitle": None},
        {"id": "btn-franja-MEDIODIA",  "label": "MEDIODÍA",  "subtitle": "14:00 - 16:15"},
        {"id": "btn-franja-TARDE",     "label": "TARDE",     "subtitle": "17:00 - 19:00"},
        {"id": "btn-franja-NOCHE",     "label": "NOCHE",     "subtitle": "20:30 - 21:00"},
    ]

    return html.Div([
        html.Div("DÉPOR HOSTELERIA", className="section-title"),
        html.Div([
            html.Button(
                children=[
                    html.Span(tab["label"]),
                    html.Span(tab["subtitle"], className="tab-subtitle") if tab["subtitle"] else None,
                ],
                id=tab["id"],
                n_clicks=1 if tab["id"] == "btn-franja-GLOBAL" else 0,
                className=f"section-tab {'active' if tab['id'] == 'btn-franja-GLOBAL' else ''}",
            ) for tab in tabs
        ], className="section-tabs"),
    ], className="section-header")


# Layout de la página
layout = html.Div([
    create_section_header(),
    dcc.Store(id="hosteleria-franja-store", data="GLOBAL"),
    dcc.Store(id="hosteleria-selected-partidos", data=[]),
    # Botón ANÁLISIS INDIVIDUAL
    html.Div(
        html.Button(
            "ANÁLISIS INDIVIDUAL",
            id="btn-analisis-individual",
            className="btn-analisis-individual",
            n_clicks=0,
        ),
        style={"padding": "0 0 4px 0"}
    ),
    # Modal de selección de partidos
    html.Div(
        id="modal-hosteleria-overlay",
        className="modal-overlay",
        children=[
            html.Div(className="modal-box", children=[
                html.Div(className="modal-header", children=[
                    html.H3("PARTIDOS DISPUTADOS", className="modal-title"),
                    html.Button(
                        "×",
                        id="btn-modal-hosteleria-close",
                        className="modal-close-btn",
                        n_clicks=0,
                    ),
                ]),
                html.Div(id="modal-hosteleria-body", className="modal-body", children=[
                    dcc.Checklist(id="modal-checklist", options=[], value=[]),
                ]),
                html.Div(className="modal-footer", children=[
                    html.Button(
                        "Cancelar",
                        id="btn-modal-hosteleria-cancelar",
                        className="modal-btn modal-btn-secondary",
                        n_clicks=0,
                    ),
                    html.Button(
                        "Aplicar selección",
                        id="btn-modal-hosteleria-aplicar",
                        className="modal-btn modal-btn-primary",
                        n_clicks=0,
                    ),
                ]),
            ]),
        ],
    ),
    dcc.Loading(
        id="loading-hosteleria",
        type="default",
        fullscreen=False,
        children=html.Div(id="content-hosteleria", children=loading_component()),
        custom_spinner=loading_component(),
    )
])


# =============================================================================
# FUNCIONES DE GRÁFICAS
# =============================================================================

def build_fig_recaudacion(df_actual):
    """Gráfica de barras: recaudación por partido con escudos."""
    rivales = df_actual['t2_name'].tolist()
    results = df_actual['result'].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(range(len(rivales))),
        y=df_actual['recaudacion_total'],
        marker_color='#f39c12',
        text=[fmt(v) + '€' for v in df_actual['recaudacion_total']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate=(
            '<b>Pedidos:</b> %{customdata[0]}<br>'
            '<b>Ticket medio:</b> %{customdata[1]}€<br>'
            '<b>Productos vendidos:</b> %{customdata[2]}'
            '<extra></extra>'
        ),
        customdata=list(zip(
            [fmt(v) for v in df_actual['n_pedidos']],
            [f"{v:.2f}" for v in df_actual['ticket_medio']],
            [fmt(v) for v in df_actual['n_productos']],
        ))
    ))

    escudos_images, result_shapes = create_escudos_with_result(rivales, results)
    max_y = df_actual['recaudacion_total'].max() * 1.15 if len(df_actual) > 0 else 100

    fig.update_layout(
        margin=dict(b=50, t=5, l=20, r=20),
        height=350,
        images=escudos_images,
        shapes=result_shapes,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(rivales))),
            ticktext=['' for _ in rivales],
            showticklabels=False,
            range=[-0.5, len(rivales) - 0.5] if len(rivales) > 0 else [0, 1]
        ),
        yaxis=dict(showticklabels=False, range=[0, max_y])
    )
    return fig


def build_fig_metodo_pago(df_metodo_actual, df_actual):
    """Gráfica stacked bar: métodos de pago por partido con escudos.
    Muestra valor€ (X%) en cada segmento. Para Abono (Club Card), que es
    muy pequeño comparado con los demás, se añade una anotación encima
    de la barra apilada para garantizar legibilidad."""
    metodo_colores = {
        'cash': '#3498db',
        'credit_card': '#2ecc71',
        'club_card': '#e74c3c',
    }
    metodo_labels = {
        'cash': 'Efectivo',
        'credit_card': 'Tarjeta',
        'club_card': 'moeDÉiro',
    }

    pivot = df_metodo_actual.pivot_table(
        index=['id_partido', 't2_name', 'schedule'],
        columns='payment_method',
        values='recaudacion',
        aggfunc='sum',
        fill_value=0
    ).reset_index().sort_values('schedule')

    rivales_met = pivot['t2_name'].tolist()
    results_met = []
    for t2 in rivales_met:
        match = df_actual[df_actual['t2_name'] == t2]
        results_met.append(match['result'].values[0] if len(match) > 0 else '0-0')

    # Calcular totales por partido para porcentajes
    metodos_disponibles = [m for m in ['cash', 'credit_card', 'club_card'] if m in pivot.columns]
    totals = pivot[metodos_disponibles].sum(axis=1).tolist()

    fig = go.Figure()

    # Cash y credit_card: barras con texto interior "valor€ (X%)"
    for metodo in ['cash', 'credit_card']:
        if metodo not in pivot.columns:
            continue
        values = pivot[metodo].tolist()
        texts = []
        for v, t in zip(values, totals):
            pct = (v / t * 100) if t > 0 else 0
            texts.append(f"{fmt(v)}€ ({pct:.1f}%)")

        fig.add_trace(go.Bar(
            name=metodo_labels.get(metodo, metodo),
            x=list(range(len(rivales_met))),
            y=values,
            marker_color=metodo_colores.get(metodo, '#95a5a6'),
            text=texts,
            textposition='inside',
            insidetextanchor='middle',
            textangle=0,
            textfont=dict(color='white', size=9, family='Montserrat', weight='bold'),
            hovertemplate=(
                f'<b>{metodo_labels.get(metodo, metodo)}:</b> '
                + '%{customdata[0]}€ (%{customdata[1]}%)<extra></extra>'
            ),
            customdata=[[fmt(v), f"{(v/t*100):.1f}" if t > 0 else "0"] for v, t in zip(values, totals)],
        ))

    # Club card: barra real (sin altura mínima artificial) + anotaciones encima
    if 'club_card' in pivot.columns:
        club_values = pivot['club_card'].tolist()

        fig.add_trace(go.Bar(
            name=metodo_labels['club_card'],
            x=list(range(len(rivales_met))),
            y=club_values,
            marker_color=metodo_colores['club_card'],
            text=[''] * len(club_values),
            hovertemplate=(
                '<b>Abono (Club Card):</b> %{customdata[0]}€ (%{customdata[1]}%)<extra></extra>'
            ),
            customdata=[[fmt(v), f"{(v/t*100):.1f}" if t > 0 else "0"] for v, t in zip(club_values, totals)],
        ))

    escudos_met, shapes_met = create_escudos_with_result(rivales_met, results_met)

    # Anotaciones para Club Card encima de cada barra apilada
    annotations = []
    if 'club_card' in pivot.columns:
        for i, (v, t) in enumerate(zip(club_values, totals)):
            pct = (v / t * 100) if t > 0 else 0
            annotations.append(dict(
                x=i, y=t,
                text=f"<b style='color:#e74c3c'>{fmt(v)}€ ({pct:.1f}%)</b>",
                showarrow=False,
                font=dict(size=9, family='Montserrat', color='#e74c3c'),
                yshift=10,
                xanchor='center',
            ))

    max_y = max(totals) * 1.12 if totals else 100

    fig.update_layout(
        barmode='stack',
        margin=dict(b=50, t=30, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        height=400,
        images=escudos_met,
        shapes=shapes_met,
        annotations=annotations,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(rivales_met))),
            ticktext=['' for _ in rivales_met],
            showticklabels=False,
            range=[-0.5, len(rivales_met) - 0.5] if len(rivales_met) > 0 else [0, 1]
        ),
        yaxis=dict(showticklabels=False, range=[0, max_y])
    )
    return fig


def build_fig_productos(df_producto, hora_filter=None, df_prod_cantina=None):
    """Top 10 productos horizontal bar. hora_filter puede ser lista de horas.
    Excluye 'Vaso Depor solidario' y bufandas."""
    df_tmp = df_producto.copy()
    df_tmp['product_name'] = df_tmp['product_name'].apply(normalizar_producto)
    if hora_filter and hora_filter != 'GLOBAL':
        if isinstance(hora_filter, list):
            df_filt = df_tmp[df_tmp['hora_exacta'].isin(hora_filter)]
        else:
            df_filt = df_tmp[df_tmp['hora_exacta'] == hora_filter]
        df_filt = df_filt.groupby('product_name').agg(
            cantidad=('cantidad', 'sum'),
            recaudacion=('recaudacion', 'sum'),
            n_pedidos=('n_pedidos', 'sum'),
        ).reset_index()
    else:
        df_filt = df_tmp.groupby('product_name').agg(
            cantidad=('cantidad', 'sum'),
            recaudacion=('recaudacion', 'sum'),
            n_pedidos=('n_pedidos', 'sum'),
        ).reset_index()

    # Excluir productos no relevantes
    df_filt = df_filt[df_filt['product_name'].apply(clasificar_producto) != 'excluido']

    top10 = df_filt.nlargest(10, 'recaudacion').sort_values('recaudacion', ascending=True)

    if top10.empty:
        fig = go.Figure()
        fig.update_layout(annotations=[{"text": "Sin datos", "showarrow": False}], height=350)
        return fig

    # Build hover with top 5 cantinas per product
    hover_texts = []
    for _, row in top10.iterrows():
        base = f"<b>{row['product_name']}</b>"
        if df_prod_cantina is not None and not df_prod_cantina.empty:
            top_cant = _get_top_cantinas_per_product(df_prod_cantina, row['product_name'], hora_filter)
            base += f"<br><br><b>Top 5 cantinas:</b><br>{top_cant}"
        hover_texts.append(base)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top10['recaudacion'],
        y=top10['product_name'],
        orientation='h',
        marker_color='#18395c',
        text=[fmt(v) + '€' for v in top10['recaudacion']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertext=hover_texts,
        hoverinfo='text',
    ))
    max_x = top10['recaudacion'].max() * 1.25 if len(top10) > 0 else 100
    fig.update_layout(
        height=350,
        margin=dict(t=10, b=20, l=180, r=40),
        xaxis=dict(showticklabels=False, range=[0, max_x]),
        yaxis=dict(tickfont=dict(size=10, family='Montserrat'))
    )
    return fig


def _get_top_products_per_cantina(df_prod_cantina, store_name, hora_filter=None, top_n=5):
    """Devuelve string con los top N productos de una cantina (excl. vaso solidario)."""
    df = df_prod_cantina[df_prod_cantina['store_name'] == store_name].copy()
    if hora_filter and hora_filter != 'GLOBAL':
        if isinstance(hora_filter, list):
            df = df[df['hora_exacta'].isin(hora_filter)]
        else:
            df = df[df['hora_exacta'] == hora_filter]
    df['product_name'] = df['product_name'].apply(normalizar_producto)
    df = df[~df['product_name'].str.lower().str.contains('vaso depor|bufanda', na=False)]
    agg = df.groupby('product_name')['cantidad'].sum().nlargest(top_n)
    if agg.empty:
        return 'Sin datos'
    return '<br>'.join([f"  {i+1}. {name} ({fmt(int(qty))} uds)" for i, (name, qty) in enumerate(agg.items())])


def build_fig_cantinas(df_cantina, hora_filter=None, df_prod_cantina=None):
    """Top 10 cantinas horizontal bar. hora_filter puede ser lista de horas."""
    if hora_filter and hora_filter != 'GLOBAL':
        if isinstance(hora_filter, list):
            df_filt = df_cantina[df_cantina['hora_exacta'].isin(hora_filter)]
        else:
            df_filt = df_cantina[df_cantina['hora_exacta'] == hora_filter]
        df_filt = df_filt.groupby(['store_id', 'store_name']).agg(
            n_pedidos=('n_pedidos', 'sum'),
            recaudacion=('recaudacion', 'sum'),
            cantidad=('cantidad', 'sum'),
        ).reset_index()
    else:
        df_filt = df_cantina.groupby(['store_id', 'store_name']).agg(
            n_pedidos=('n_pedidos', 'sum'),
            recaudacion=('recaudacion', 'sum'),
            cantidad=('cantidad', 'sum'),
        ).reset_index()

    top10 = df_filt.nlargest(10, 'recaudacion').sort_values('recaudacion', ascending=True)

    if top10.empty:
        fig = go.Figure()
        fig.update_layout(annotations=[{"text": "Sin datos", "showarrow": False}], height=350)
        return fig

    # Build hover with top 5 products per cantina
    hover_texts = []
    for _, row in top10.iterrows():
        base = f"<b>{row['store_name']}</b>"
        if df_prod_cantina is not None and not df_prod_cantina.empty:
            top_prods = _get_top_products_per_cantina(df_prod_cantina, row['store_name'], hora_filter)
            base += f"<br><br><b>Top 5 productos:</b><br>{top_prods}"
        hover_texts.append(base)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top10['recaudacion'],
        y=top10['store_name'],
        orientation='h',
        marker_color='#18395c',
        text=[fmt(v) + '€' for v in top10['recaudacion']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertext=hover_texts,
        hoverinfo='text',
    ))
    max_x = top10['recaudacion'].max() * 1.25 if len(top10) > 0 else 100
    fig.update_layout(
        height=350,
        margin=dict(t=10, b=20, l=100, r=40),
        xaxis=dict(showticklabels=False, range=[0, max_x]),
        yaxis=dict(tickfont=dict(size=10, family='Montserrat'))
    )
    return fig


def _get_top_cantinas_per_product(df_prod_cantina, product_name, hora_filter=None, top_n=5):
    """Devuelve string con las top N cantinas donde más se vende un producto."""
    df = df_prod_cantina.copy()
    df['product_name'] = df['product_name'].apply(normalizar_producto)
    df = df[df['product_name'] == product_name]
    if hora_filter and hora_filter != 'GLOBAL':
        if isinstance(hora_filter, list):
            df = df[df['hora_exacta'].isin(hora_filter)]
        else:
            df = df[df['hora_exacta'] == hora_filter]
    agg = df.groupby('store_name')['cantidad'].sum().nlargest(top_n)
    if agg.empty:
        return 'Sin datos'
    return '<br>'.join([f"  {i+1}. {name} ({fmt(int(qty))} uds)" for i, (name, qty) in enumerate(agg.items())])


def _build_fig_categoria(df_producto, categoria, hora_filter, color, title_suffix,
                          n_partidos=1, df_prod_cantina=None):
    """Top 10 productos de una categoría (bebida/comestible) por cantidad promedio.
    n_partidos se usa para calcular promedios por partido."""
    df_tmp = df_producto.copy()
    df_tmp['product_name'] = df_tmp['product_name'].apply(normalizar_producto)
    if hora_filter and hora_filter != 'GLOBAL':
        if isinstance(hora_filter, list):
            df_filt = df_tmp[df_tmp['hora_exacta'].isin(hora_filter)]
        else:
            df_filt = df_tmp[df_tmp['hora_exacta'] == hora_filter]
        df_filt = df_filt.groupby('product_name').agg(
            cantidad=('cantidad', 'sum'),
            recaudacion=('recaudacion', 'sum'),
            n_pedidos=('n_pedidos', 'sum'),
        ).reset_index()
    else:
        df_filt = df_tmp.groupby('product_name').agg(
            cantidad=('cantidad', 'sum'),
            recaudacion=('recaudacion', 'sum'),
            n_pedidos=('n_pedidos', 'sum'),
        ).reset_index()

    df_filt = df_filt[df_filt['product_name'].apply(clasificar_producto) == categoria]

    # Calcular promedios por partido
    n = max(n_partidos, 1)
    df_filt['cantidad_avg'] = df_filt['cantidad'] / n
    df_filt['recaudacion_avg'] = df_filt['recaudacion'] / n

    top10 = df_filt.nlargest(10, 'cantidad_avg').sort_values('cantidad_avg', ascending=True)

    if top10.empty:
        fig = go.Figure()
        fig.update_layout(annotations=[{"text": "Sin datos", "showarrow": False}], height=350)
        return fig

    # Build hover with top 5 cantinas per product (sin uds/facturación, ya en etiqueta)
    hover_texts = []
    for _, row in top10.iterrows():
        base = f"<b>{row['product_name']}</b>"
        if df_prod_cantina is not None and not df_prod_cantina.empty:
            top_cant = _get_top_cantinas_per_product(df_prod_cantina, row['product_name'], hora_filter)
            base += f"<br><br><b>Top 5 cantinas:</b><br>{top_cant}"
        hover_texts.append(base)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top10['cantidad_avg'],
        y=top10['product_name'],
        orientation='h',
        marker_color=color,
        text=[f"{v:.1f} uds · {r:.0f}€" for v, r in zip(top10['cantidad_avg'], top10['recaudacion_avg'])],
        textposition='outside',
        textfont=dict(color='#333', size=9, family='Montserrat', weight='bold'),
        hovertext=hover_texts,
        hoverinfo='text',
    ))
    max_x = top10['cantidad_avg'].max() * 1.35 if len(top10) > 0 else 100
    fig.update_layout(
        height=350,
        margin=dict(t=10, b=20, l=180, r=80),
        xaxis=dict(showticklabels=False, range=[0, max_x]),
        yaxis=dict(tickfont=dict(size=10, family='Montserrat'))
    )
    return fig


def build_fig_bebidas(df_producto, hora_filter=None, n_partidos=1, df_prod_cantina=None):
    """Top 10 bebidas más consumidas (promedio por partido)."""
    return _build_fig_categoria(df_producto, 'bebida', hora_filter, '#18395c', 'Bebidas',
                                 n_partidos, df_prod_cantina)


def build_fig_comestibles(df_producto, hora_filter=None, n_partidos=1, df_prod_cantina=None):
    """Top 10 comestibles más consumidos (promedio por partido)."""
    return _build_fig_categoria(df_producto, 'comestible', hora_filter, '#18395c', 'Comestibles',
                                 n_partidos, df_prod_cantina)


def build_fig_recaudacion_media_hora(df_actual):
    """Gráfica GLOBAL: recaudación media por hora de inicio."""
    rivals_map = df_actual.groupby('hora_exacta')['t2_name'].apply(list).to_dict()

    agg = df_actual.groupby('hora_exacta').agg(
        recaudacion_media=('recaudacion_total', 'mean'),
        n_partidos=('id_partido', 'nunique'),
        pedidos_medio=('n_pedidos', 'mean'),
        ticket_medio=('ticket_medio', 'mean'),
    ).reset_index().sort_values('hora_exacta')

    colores = ['#f39c12' if v == agg['recaudacion_media'].max() else '#18395c' for v in agg['recaudacion_media']]

    hover_texts = [
        f"<b>Hora: {h}</b><br>Recaudación media: {fmt(r)}€<br>"
        f"Partidos: {int(n)} ({', '.join(rivals_map.get(h, []))})"
        for h, r, n in zip(agg['hora_exacta'], agg['recaudacion_media'], agg['n_partidos'])
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg['hora_exacta'],
        y=agg['recaudacion_media'],
        marker_color=colores,
        text=[fmt(v) + '€' for v in agg['recaudacion_media']],
        textposition='outside',
        textfont=dict(color='#333', size=11, family='Montserrat', weight='bold'),
        hovertext=hover_texts,
        hoverinfo='text',
    ))
    max_y = agg['recaudacion_media'].max() * 1.15 if len(agg) > 0 else 100
    fig.update_layout(
        height=350,
        margin=dict(t=10, b=30, l=20, r=20),
        xaxis=dict(tickfont=dict(size=12, family='Montserrat')),
        yaxis=dict(showticklabels=False, range=[0, max_y])
    )
    return fig


def build_fig_ticket_medio_hora(df_actual):
    """Gráfica GLOBAL: ticket medio por hora de inicio."""
    rivals_map = df_actual.groupby('hora_exacta')['t2_name'].apply(list).to_dict()

    agg = df_actual.groupby('hora_exacta').agg(
        ticket_medio=('ticket_medio', 'mean'),
        n_partidos=('id_partido', 'nunique'),
    ).reset_index().sort_values('hora_exacta')

    colores = ['#f39c12' if v == agg['ticket_medio'].max() else '#18395c' for v in agg['ticket_medio']]

    hover_texts = [
        f"<b>Hora: {h}</b><br>Ticket medio: {v:.2f}€<br>"
        f"Partidos: {int(n)} ({', '.join(rivals_map.get(h, []))})"
        for h, v, n in zip(agg['hora_exacta'], agg['ticket_medio'], agg['n_partidos'])
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg['hora_exacta'],
        y=agg['ticket_medio'],
        marker_color=colores,
        text=[f"{v:.2f}€" for v in agg['ticket_medio']],
        textposition='outside',
        textfont=dict(color='#333', size=11, family='Montserrat', weight='bold'),
        hovertext=hover_texts,
        hoverinfo='text',
    ))
    max_y = agg['ticket_medio'].max() * 1.15 if len(agg) > 0 else 20
    fig.update_layout(
        height=350,
        margin=dict(t=10, b=30, l=20, r=20),
        xaxis=dict(tickfont=dict(size=12, family='Montserrat')),
        yaxis=dict(showticklabels=False, range=[0, max_y])
    )
    return fig


def build_fig_ticket_medio_metodo(df_metodo_actual):
    """Gráfica GLOBAL: ticket medio por método de pago (excluye 'accumulated')."""
    metodo_labels = {
        'cash': 'Efectivo',
        'credit_card': 'Tarjeta',
        'club_card': 'moeDEiro',
    }

    # Filtrar accumulated (sistema de cuenta de palcos VIP)
    df_filtered = df_metodo_actual[df_metodo_actual['payment_method'] != 'accumulated'].copy()
    
    agg = df_filtered.groupby('payment_method').agg(
        recaudacion=('recaudacion', 'sum'),
        n_pedidos=('n_pedidos', 'sum'),
    ).reset_index()
    agg['ticket_medio'] = (agg['recaudacion'] / agg['n_pedidos']).round(2)
    agg['label'] = agg['payment_method'].map(metodo_labels).fillna(agg['payment_method'])
    agg = agg.sort_values('ticket_medio', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg['ticket_medio'],
        y=agg['label'],
        orientation='h',
        marker_color='#18395c',
        width=0.4,
        text=[f"{v:.2f}€" for v in agg['ticket_medio']],
        textposition='outside',
        textfont=dict(color='#333', size=11, family='Montserrat', weight='bold'),
        hovertext=[
            f"<b>{l}</b><br>Ticket medio: {tm:.2f}€<br>Pedidos: {fmt(int(np))}<br>Recaudación: {fmt(r)}€"
            for l, tm, np, r in zip(agg['label'], agg['ticket_medio'], agg['n_pedidos'], agg['recaudacion'])
        ],
        hoverinfo='text',
    ))
    max_x = agg['ticket_medio'].max() * 1.25 if len(agg) > 0 else 20
    fig.update_layout(
        height=280,
        margin=dict(t=10, b=30, l=100, r=40),
        xaxis=dict(showticklabels=False, range=[0, max_x]),
        yaxis=dict(tickfont=dict(size=12, family='Montserrat')),
    )
    return fig


def build_fig_metodo_pago_pie(df_metodo_filtered):
    """Pie chart: % de facturación por método de pago."""
    metodo_labels = {
        'cash': 'Efectivo',
        'credit_card': 'Tarjeta',
        'club_card': 'moeDÉiro',
    }
    metodo_colores = {
        'cash': '#3498db',
        'credit_card': '#2ecc71',
        'club_card': '#e74c3c',
    }

    df_f = df_metodo_filtered[df_metodo_filtered['payment_method'] != 'accumulated'].copy()
    agg = df_f.groupby('payment_method')['recaudacion'].sum().reset_index()
    agg['label'] = agg['payment_method'].map(metodo_labels).fillna(agg['payment_method'])
    agg['color'] = agg['payment_method'].map(metodo_colores).fillna('#95a5a6')

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=agg['label'],
        values=agg['recaudacion'],
        marker=dict(colors=agg['color'].tolist()),
        textinfo='label+percent',
        textfont=dict(size=13, family='Montserrat', weight='bold'),
        hovertemplate='<b>%{label}</b><br>Recaudación: %{value:,.0f}€<br>%{percent}<extra></extra>',
        hole=0.35,
    ))
    fig.update_layout(
        height=350,
        margin=dict(t=10, b=20, l=20, r=20),
        showlegend=False,
    )
    return fig


# =============================================================================
# LAYOUT BUILDERS
# =============================================================================

def create_global_content(kpis, fig_recaudacion, fig_productos, fig_cantinas,
                          fig_rec_hora, fig_ticket_hora, fig_ticket_metodo,
                          fig_pct_metodo=None):
    """Contenido para vista GLOBAL."""
    # Fila 3: Ticket medio + % facturación por método de pago (lado a lado)
    if fig_pct_metodo is not None:
        fila_metodo = html.Div([
            html.Div([
                html.H4("Ticket Medio por Método de Pago"),
                dcc.Graph(figure=fig_ticket_metodo, config={'displayModeBar': False})
            ], className="graph-card"),
            html.Div([
                html.H4("% Facturación por Método de Pago"),
                dcc.Graph(figure=fig_pct_metodo, config={'displayModeBar': False})
            ], className="graph-card"),
        ], className="graphs-row")
    else:
        fila_metodo = html.Div([
            html.Div([
                html.H4("Ticket Medio por Método de Pago"),
                dcc.Graph(figure=fig_ticket_metodo, config={'displayModeBar': False})
            ], className="graph-card full-width"),
        ], className="graphs-row")

    return html.Div([
        html.Div(kpis, className="kpis-container"),
        html.Div([
            # Fila 1: Recaudación por partido
            html.Div([
                html.Div([
                    html.H4("Recaudación por Partido"),
                    dcc.Graph(figure=fig_recaudacion, config={'displayModeBar': False})
                ], className="graph-card full-width"),
            ], className="graphs-row"),
            # Fila 2: Insights por hora (solo GLOBAL)
            html.Div([
                html.Div([
                    html.H4("Recaudación Media por Hora de Inicio"),
                    dcc.Graph(figure=fig_rec_hora, config={'displayModeBar': False})
                ], className="graph-card"),
                html.Div([
                    html.H4("Ticket Medio por Hora de Inicio"),
                    dcc.Graph(figure=fig_ticket_hora, config={'displayModeBar': False})
                ], className="graph-card"),
            ], className="graphs-row"),
            # Fila 3: Métodos de pago
            fila_metodo,
            # Fila 4: Top productos y cantinas (al fondo)
            html.Div([
                html.Div([
                    html.H4("Top 10 Productos más Vendidos"),
                    dcc.Graph(figure=fig_productos, config={'displayModeBar': False}),
                    html.P("*Excluyendo la venta de vasos solidarios",
                           style={"fontSize": "0.7rem", "color": "#999", "fontStyle": "italic",
                                  "textAlign": "center", "marginTop": "2px"})
                ], className="graph-card"),
                html.Div([
                    html.H4("Top 10 Cantinas más rentables"),
                    dcc.Graph(figure=fig_cantinas, config={'displayModeBar': False})
                ], className="graph-card"),
            ], className="graphs-row"),
        ], className="graphs-container"),
    ], className="page-content-container")


def create_franja_content(kpis, fig_recaudacion, fig_cantinas,
                          fig_bebidas, fig_comestibles):
    """Contenido para vista filtrada por franja horaria."""
    return html.Div([
        html.Div(kpis, className="kpis-container"),
        html.Div([
            # Fila 1: Recaudación por partido
            html.Div([
                html.Div([
                    html.H4("Recaudación por Partido"),
                    dcc.Graph(figure=fig_recaudacion, config={'displayModeBar': False})
                ], className="graph-card full-width"),
            ], className="graphs-row"),
            # Fila 2: Bebidas y comestibles (promedios)
            html.Div([
                html.Div([
                    html.H4("Top 10 Bebidas más Consumidas"),
                    dcc.Graph(figure=fig_bebidas, config={'displayModeBar': False})
                ], className="graph-card"),
                html.Div([
                    html.H4("Top 10 Comestibles más Consumidos"),
                    dcc.Graph(figure=fig_comestibles, config={'displayModeBar': False})
                ], className="graph-card"),
            ], className="graphs-row"),
            # Fila 3: Cantinas
            html.Div([
                html.Div([
                    html.H4("Top 10 Cantinas más rentables"),
                    dcc.Graph(figure=fig_cantinas, config={'displayModeBar': False})
                ], className="graph-card full-width"),
            ], className="graphs-row"),
        ], className="graphs-container"),
    ], className="page-content-container")


# =============================================================================
# CALLBACKS
# =============================================================================

FRANJA_BTNS = ["btn-franja-GLOBAL", "btn-franja-MEDIODIA", "btn-franja-TARDE", "btn-franja-NOCHE"]


@callback(
    Output("modal-hosteleria-body", "children"),
    Input("modal-hosteleria-overlay", "className"),
    State("hosteleria-selected-partidos", "data"),
    prevent_initial_call=True,
)
def populate_modal(class_name, current_selection):
    """Rellena la lista de partidos en el modal cada vez que se abre."""
    if not class_name or "visible" not in class_name:
        return no_update
    try:
        df = get_pre_hosteleria_partido()
        df['schedule'] = pd.to_datetime(df['schedule'], errors='coerce')
        df_actual = df[df['temporada'] == 'actual'].sort_values('schedule')
        if df_actual.empty:
            return html.P("No hay partidos disponibles.", style={"color": "#888", "padding": "10px"})
        options = []
        for _, row in df_actual.iterrows():
            fecha = row['schedule'].strftime('%d/%m/%Y')
            hora = row['schedule'].strftime('%H:%M')
            dia = DIAS_ES.get(str(row.get('dia_semana', '')), str(row.get('dia_semana', '')))
            escudo_path = get_escudo_path(row['t2_name'])
            label = html.Div([
                html.Img(src=escudo_path, className="match-escudo") if escudo_path
                    else html.Div(style={"width": "30px", "flexShrink": "0"}),
                html.Div([
                    html.Span(row['t2_name'], className="match-rival-name"),
                    html.Span(f"{dia}  ·  {fecha}  ·  {hora}", className="match-details"),
                ], className="match-info"),
            ], style={"display": "flex", "alignItems": "center", "gap": "10px"})
            options.append({"label": label, "value": int(row['id_partido'])})
        return dcc.Checklist(
            id="modal-checklist",
            options=options,
            value=list(current_selection) if current_selection else [],
            inputStyle={
                "marginRight": "10px", "width": "18px", "height": "18px",
                "accentColor": "#1a3a5c", "cursor": "pointer", "flexShrink": "0",
            },
            labelStyle={
                "display": "flex", "alignItems": "center", "padding": "8px 6px",
                "cursor": "pointer", "borderBottom": "1px solid #f0f0f0",
                "width": "100%",
            },
        )
    except Exception as e:
        return html.P(f"Error cargando partidos: {e}", style={"color": "red", "padding": "10px"})


@callback(
    Output("modal-hosteleria-overlay", "className"),
    Output("hosteleria-selected-partidos", "data"),
    Input("btn-analisis-individual", "n_clicks"),
    Input("btn-modal-hosteleria-close", "n_clicks"),
    Input("btn-modal-hosteleria-cancelar", "n_clicks"),
    Input("btn-modal-hosteleria-aplicar", "n_clicks"),
    State("modal-checklist", "value"),
    State("hosteleria-selected-partidos", "data"),
    prevent_initial_call=True,
)
def manage_modal(open_c, close_c, cancel_c, apply_c, checklist_value, current_selection):
    """Gestiona apertura/cierre del modal y aplica la selección.

    Si hay selección activa, el botón principal limpia; si no, abre el modal.
    """
    trigger = ctx.triggered_id
    if trigger == "btn-analisis-individual":
        if current_selection:
            return no_update, []  # limpiar selección sin abrir modal
        return "modal-overlay visible", no_update  # abrir modal
    if trigger == "btn-modal-hosteleria-aplicar":
        return "modal-overlay", checklist_value or []
    return "modal-overlay", no_update


@callback(
    Output("btn-analisis-individual", "children"),
    Output("btn-analisis-individual", "className"),
    Input("hosteleria-selected-partidos", "data"),
)
def update_btn_label(selected_ids):
    """Actualiza el texto del botón mostrando cuántos partidos están seleccionados."""
    if selected_ids:
        n = len(selected_ids)
        label = "LIMPIAR SELECCIÓN" if n == 0 else f"ANÁLISIS INDIVIDUAL"
        return [
            label,
            html.Span(f"{n} partido{'s' if n != 1 else ''}", className="selection-pill"),
        ], "btn-analisis-individual active"
    return "ANÁLISIS INDIVIDUAL", "btn-analisis-individual"


@callback(
    [Output("hosteleria-franja-store", "data")] + [Output(b, "className") for b in FRANJA_BTNS],
    [Input(b, "n_clicks") for b in FRANJA_BTNS],
    prevent_initial_call=True
)
def update_franja_store(*args):
    """Actualiza la franja seleccionada y el estado activo de los botones."""
    trigger = ctx.triggered_id
    selected = trigger.replace("btn-franja-", "") if trigger and trigger.startswith("btn-franja-") else "GLOBAL"
    classes = [
        "section-tab active" if b == trigger else "section-tab"
        for b in FRANJA_BTNS
    ]
    return [selected] + classes


@callback(
    Output("content-hosteleria", "children"),
    Input("hosteleria-franja-store", "data"),
    Input("hosteleria-selected-partidos", "data"),
)
def update_page(franja_selected, selected_partidos):
    """Actualiza todas las gráficas según la franja seleccionada o los partidos individuales."""
    if franja_selected is None:
        franja_selected = "GLOBAL"

    try:
        df_partido = get_pre_hosteleria_partido()
        df_producto = get_pre_hosteleria_producto()
        df_cantina = get_pre_hosteleria_cantina()
        df_metodo = get_pre_hosteleria_metodo_pago()
        try:
            df_prod_cantina = get_pre_hosteleria_producto_cantina()
        except Exception:
            df_prod_cantina = pd.DataFrame()

        if df_partido.empty:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                annotations=[{"text": "No hay datos disponibles. Ejecuta sync_data.py primero.", "showarrow": False}]
            )
            return html.Div("No hay datos disponibles.")

        df_partido['schedule'] = pd.to_datetime(df_partido['schedule'], errors='coerce')
        df_metodo['schedule'] = pd.to_datetime(df_metodo['schedule'], errors='coerce')

        # Datos de asistencia para KPI "Ingreso por Asistente"
        try:
            df_asistencia = get_pre_asistencia_partido()
        except Exception:
            df_asistencia = pd.DataFrame()

        df_actual = df_partido[df_partido['temporada'] == 'actual'].sort_values('schedule')
        df_anterior = df_partido[df_partido['temporada'] == 'anterior']

        if df_actual.empty:
            return html.Div("No hay datos para la temporada actual.")

        # =====================================================================
        # MODO ANÁLISIS INDIVIDUAL: filtra por partidos seleccionados
        # =====================================================================
        is_individual = bool(selected_partidos)
        if is_individual:
            df_actual_base = df_actual[df_actual['id_partido'].isin(selected_partidos)]
            if df_actual_base.empty:
                return html.Div(
                    "No hay datos para los partidos seleccionados.",
                    style={"padding": "40px", "textAlign": "center", "color": "#888"}
                )
            # Filtrar tablas de producto/cantina/metodo por id_partido
            if 'id_partido' in df_producto.columns:
                df_prod_f = df_producto[df_producto['id_partido'].isin(selected_partidos)]
            else:
                df_prod_f = df_producto
            if 'id_partido' in df_cantina.columns:
                df_cant_f = df_cantina[df_cantina['id_partido'].isin(selected_partidos)]
            else:
                df_cant_f = df_cantina
            if not df_prod_cantina.empty and 'id_partido' in df_prod_cantina.columns:
                df_pc_f = df_prod_cantina[df_prod_cantina['id_partido'].isin(selected_partidos)]
            else:
                df_pc_f = df_prod_cantina
            df_metodo_f = df_metodo[
                (df_metodo['temporada'] == 'actual') &
                (df_metodo['id_partido'].isin(selected_partidos))
            ] if 'id_partido' in df_metodo.columns else df_metodo[df_metodo['temporada'] == 'actual']

            # KPIs (sin comparativa, sólo partidos seleccionados)
            total_pedidos_i = df_actual_base['n_pedidos'].sum()
            total_rec_i = df_actual_base['recaudacion_total'].sum()
            ticket_medio_i = total_rec_i / total_pedidos_i if total_pedidos_i > 0 else 0
            prom_pedidos_i = df_actual_base['n_pedidos'].mean()
            rec_promedio_i = df_actual_base['recaudacion_total'].mean()

            # Ingreso por asistente (individual)
            ingreso_asist_i = 0
            if not df_asistencia.empty:
                df_m = df_actual_base.merge(
                    df_asistencia[['id_partido', 'total_espectadores']], on='id_partido', how='left'
                ).dropna(subset=['total_espectadores'])
                total_esp_i = df_m['total_espectadores'].sum()
                ingreso_asist_i = (df_m['recaudacion_total'].sum() / total_esp_i) if total_esp_i > 0 else 0

            rivales_label = ', '.join(df_actual_base.sort_values('schedule')['t2_name'].tolist())
            banner = html.Div(
                html.Span([
                    html.Strong(f"ANÁLISIS INDIVIDUAL — "),
                    f"{len(df_actual_base)} partido{'s' if len(df_actual_base) != 1 else ''}: {rivales_label}"
                ]),
                style={
                    "background": "#e8f0fa", "border": "1px solid #1a3a5c",
                    "borderRadius": "6px", "padding": "8px 14px",
                    "marginBottom": "10px", "fontSize": "0.82rem",
                    "color": "#1a3a5c", "fontFamily": "Montserrat, sans-serif"
                }
            )

            TT = {
                'pedidos': "Nº total de pedidos en los ambigús para los partidos seleccionados.",
                'prom_ped': "Media de pedidos por partido (Total Pedidos ÷ Nº Partidos seleccionados).",
                'ticket': "Gasto medio por pedido (Recaudación Total ÷ Total Pedidos).",
                'rec_total': "Suma de ingresos de hostelería (precio × cantidad). Se excluyen reembolsos y pagos pendientes.",
                'rec_prom': "Media de recaudación por partido (Recaudación Total ÷ Nº Partidos).",
                'ingreso_asist': "Recaudación total hostelería ÷ Total espectadores. Indica el gasto medio en ambigús por cada espectador.",
            }

            kpis = html.Div([
                banner,
                html.Div([
                    create_kpi_card(total_pedidos_i, None, "Total Pedidos", tooltip=TT['pedidos']),
                    create_kpi_card(prom_pedidos_i, None, "Promedio Pedidos", tooltip=TT['prom_ped']),
                    create_kpi_card(ticket_medio_i, None, "Ticket Medio", "euros", tooltip=TT['ticket']),
                    create_kpi_card(total_rec_i, None, "Recaudación Total", "euros", tooltip=TT['rec_total']),
                    create_kpi_card(rec_promedio_i, None, "Recaudación Promedio", "euros", tooltip=TT['rec_prom']),
                    create_kpi_card(ingreso_asist_i, None, "Ingreso por Asistente", "euros", tooltip=TT['ingreso_asist']),
                ], className="kpis-row"),
            ])

            fig_rec = build_fig_recaudacion(df_actual_base)
            fig_prod = build_fig_productos(df_prod_f, df_prod_cantina=df_pc_f)
            fig_cant = build_fig_cantinas(df_cant_f, df_prod_cantina=df_pc_f)
            fig_rec_hora = build_fig_recaudacion_media_hora(df_actual_base)
            fig_ticket_hora = build_fig_ticket_medio_hora(df_actual_base)
            fig_ticket_metodo = build_fig_ticket_medio_metodo(df_metodo_f)
            fig_pct_metodo = build_fig_metodo_pago_pie(df_metodo_f)

            return create_global_content(kpis, fig_rec, fig_prod, fig_cant,
                                         fig_rec_hora, fig_ticket_hora, fig_ticket_metodo,
                                         fig_pct_metodo)

        # =====================================================================
        # VISTA GLOBAL
        # =====================================================================
        if franja_selected == "GLOBAL":
            # KPIs con comparativa temporada anterior
            total_pedidos = df_actual['n_pedidos'].sum()
            total_recaudacion = df_actual['recaudacion_total'].sum()
            ticket_medio = total_recaudacion / total_pedidos if total_pedidos > 0 else 0

            n_partidos_global = len(df_actual)
            promedio_pedidos = df_actual['n_pedidos'].mean()
            recaudacion_promedio = df_actual['recaudacion_total'].mean()

            total_pedidos_ant = df_anterior['n_pedidos'].sum()
            total_recaudacion_ant = df_anterior['recaudacion_total'].sum()
            ticket_medio_ant = total_recaudacion_ant / total_pedidos_ant if total_pedidos_ant > 0 else 0
            promedio_pedidos_ant = df_anterior['n_pedidos'].mean() if len(df_anterior) > 0 else 0
            recaudacion_promedio_ant = df_anterior['recaudacion_total'].mean() if len(df_anterior) > 0 else 0

            # Ingreso por asistente
            ingreso_asist, ingreso_asist_ant = 0, 0
            if not df_asistencia.empty:
                df_m = df_actual.merge(
                    df_asistencia[['id_partido', 'total_espectadores']], on='id_partido', how='left'
                ).dropna(subset=['total_espectadores'])
                t_esp = df_m['total_espectadores'].sum()
                ingreso_asist = (df_m['recaudacion_total'].sum() / t_esp) if t_esp > 0 else 0
                df_m_ant = df_anterior.merge(
                    df_asistencia[['id_partido', 'total_espectadores']], on='id_partido', how='left'
                ).dropna(subset=['total_espectadores'])
                t_esp_ant = df_m_ant['total_espectadores'].sum()
                ingreso_asist_ant = (df_m_ant['recaudacion_total'].sum() / t_esp_ant) if t_esp_ant > 0 else 0

            TT = {
                'pedidos': "Nº total de pedidos realizados en los ambigús del estadio durante todos los partidos de la temporada.",
                'prom_ped': "Media de pedidos por partido. Cálculo: Total Pedidos ÷ Nº Partidos disputados.",
                'ticket': "Gasto medio por pedido. Cálculo: Recaudación Total ÷ Total Pedidos.",
                'rec_total': "Suma de ingresos de hostelería (precio × cantidad) de todos los partidos. Se excluyen reembolsos y pagos pendientes.",
                'rec_prom': "Media de recaudación por partido. Cálculo: Recaudación Total ÷ Nº Partidos disputados.",
                'ingreso_asist': "Gasto medio en ambigús por cada espectador. Cálculo: Recaudación total hostelería ÷ Total espectadores.",
            }

            kpis = html.Div([
                create_kpi_card(total_pedidos, total_pedidos_ant, "Total Pedidos", tooltip=TT['pedidos']),
                create_kpi_card(promedio_pedidos, promedio_pedidos_ant, "Promedio Pedidos", tooltip=TT['prom_ped']),
                create_kpi_card(ticket_medio, ticket_medio_ant, "Ticket Medio", "euros", tooltip=TT['ticket']),
                create_kpi_card(total_recaudacion, total_recaudacion_ant, "Recaudación Total", "euros", tooltip=TT['rec_total']),
                create_kpi_card(recaudacion_promedio, recaudacion_promedio_ant, "Recaudación Promedio", "euros", tooltip=TT['rec_prom']),
                create_kpi_card(ingreso_asist, ingreso_asist_ant, "Ingreso por Asistente", "euros", tooltip=TT['ingreso_asist']),
            ], className="kpis-row")

            df_metodo_actual = df_metodo[df_metodo['temporada'] == 'actual']
            fig_rec = build_fig_recaudacion(df_actual)
            fig_prod = build_fig_productos(df_producto, df_prod_cantina=df_prod_cantina)
            fig_cant = build_fig_cantinas(df_cantina, df_prod_cantina=df_prod_cantina)
            fig_rec_hora = build_fig_recaudacion_media_hora(df_actual)
            fig_ticket_hora = build_fig_ticket_medio_hora(df_actual)
            fig_ticket_metodo = build_fig_ticket_medio_metodo(df_metodo_actual)
            fig_pct_metodo = build_fig_metodo_pago_pie(df_metodo_actual)

            return create_global_content(kpis, fig_rec, fig_prod, fig_cant,
                                         fig_rec_hora, fig_ticket_hora, fig_ticket_metodo,
                                         fig_pct_metodo)

        # =====================================================================
        # VISTA POR FRANJA
        # =====================================================================
        else:
            franja_info = FRANJAS.get(franja_selected)
            if not franja_info:
                return html.Div(f"Franja '{franja_selected}' no reconocida.")

            horas_franja = franja_info['horas']
            df_franja = df_actual[df_actual['hora_exacta'].isin(horas_franja)]

            if df_franja.empty:
                return html.Div(f"No hay partidos disputados en franja {franja_info['label']}.")

            # Medias globales para comparativa
            media_pedidos = df_actual['n_pedidos'].mean()
            media_recaudacion = df_actual['recaudacion_total'].mean()
            media_ticket = (df_actual['recaudacion_total'].sum() / df_actual['n_pedidos'].sum()) if df_actual['n_pedidos'].sum() > 0 else 0

            # KPIs de esta franja vs media global (promedios)
            pedidos_franja = df_franja['n_pedidos'].mean()
            recaudacion_franja = df_franja['recaudacion_total'].mean()
            ticket_franja = (df_franja['recaudacion_total'].sum() / df_franja['n_pedidos'].sum()) if df_franja['n_pedidos'].sum() > 0 else 0
            n_partidos_franja = len(df_franja)

            TT_F = {
                'pedidos': "Media de pedidos por partido en partidos de esta franja horaria.",
                'ticket': "Gasto medio por pedido en partidos de esta franja horaria.",
                'rec': "Media de recaudación por partido en esta franja horaria.",
            }
            kpis = html.Div([
                create_kpi_card_hora(pedidos_franja, f"Pedidos Medio ({n_partidos_franja} partidos)", media_pedidos, tooltip=TT_F['pedidos']),
                create_kpi_card_hora(ticket_franja, "Ticket Medio", media_ticket, "euros", tooltip=TT_F['ticket']),
                create_kpi_card_hora(recaudacion_franja, "Recaudación Media", media_recaudacion, "euros", tooltip=TT_F['rec']),
            ], className="kpis-row")

            # Gráficas
            fig_rec = build_fig_recaudacion(df_franja)
            fig_cant = build_fig_cantinas(df_cantina, horas_franja, df_prod_cantina)
            fig_beb = build_fig_bebidas(df_producto, horas_franja, n_partidos_franja, df_prod_cantina)
            fig_com = build_fig_comestibles(df_producto, horas_franja, n_partidos_franja, df_prod_cantina)

            return create_franja_content(kpis, fig_rec, fig_cant,
                                         fig_beb, fig_com)

    except Exception as e:
        print(f"Error en hosteleria: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"Error: {str(e)}")
