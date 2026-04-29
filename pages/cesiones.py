"""
Página de Cesiones - Estadio Abanca-Riazor
==========================================
Análisis de cesiones de abonos por partido
"""

import dash
from dash import html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from database import get_pre_cesiones_partido, get_pre_cesiones_recaudacion, get_pre_cesiones_sector
from components import temporada_toggle

dash.register_page(__name__, path="/estadio/cesiones", name="Cesiones")

# Fechas de temporadas
INICIO_TEMP_ACTUAL = datetime(2025, 8, 1)
INICIO_TEMP_ANTERIOR = datetime(2024, 8, 1)

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
    # Rivales temporada 24/25 (no presentes en 25/26)
    'Cartagena': 'Cartagena.png',
    'FC Cartagena': 'Cartagena.png',
    'Elche': 'Elche.png',
    'Elche CF': 'Elche.png',
    'Eldense': 'Eldense.png',
    'CD Eldense': 'Eldense.png',
    'Le Havre': 'Le Havre.png',
    'Levante': 'Levante.png',
    'Levante UD': 'Levante.png',
    # Rivales 24/25 cuyos archivos PNG aún no están en assets/Escudos/
    'Tenerife': 'Tenerife.png',
    'CD Tenerife': 'Tenerife.png',
    'Real Oviedo': 'Real Oviedo.png',
    'Racing Ferrol': 'Racing Ferrol.png',
    'Racing de Ferrol': 'Racing Ferrol.png',
    'Unionistas': 'Unionistas.png',
    'Unionistas CF': 'Unionistas.png',
}


def get_escudo_path(team_name):
    """Obtiene la ruta del escudo para un equipo."""
    escudo_file = ESCUDOS_MAP.get(team_name)
    if escudo_file:
        return f"/assets/Escudos/{escudo_file}"
    return None


def get_data():
    """Obtiene datos pre-calculados de cesiones por partido."""
    try:
        df = get_pre_cesiones_partido()
        if df.empty:
            return pd.DataFrame()
        df['schedule'] = pd.to_datetime(df['schedule'], errors='coerce')
        return df
    except Exception as e:
        print(f"Error obteniendo datos: {e}")
        return pd.DataFrame()


def format_with_dots(val):
    """Formatea número con puntos como separador de miles."""
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
    if not text:
        return None
    return html.Div([
        html.Span("?", className="kpi-tooltip-icon"),
        html.Div(text, className="kpi-tooltip-box"),
    ], className="kpi-tooltip-wrapper")


def create_kpi_card(valor_actual, valor_anterior, label, formato="numero",
                     tooltip=None, comparar=True):
    """Crea una tarjeta KPI.

    Si `comparar=True` muestra el valor actual + % diferencia + dato anterior.
    Si `comparar=False` muestra únicamente el valor agregado sin comparativa
    (usado al activar el toggle "Temporada 24/25" para mostrar solo el dato
    de esa temporada).
    """
    label_children = [label]
    if tooltip:
        label_children.append(_kpi_tooltip(tooltip))
    label_div = html.Div(label_children, className="kpi-label-top",
                         style={"display": "flex", "alignItems": "center",
                                "justifyContent": "center", "gap": "5px"})

    if formato == "euros":
        texto_actual = f"{format_with_dots(valor_actual)}€"
        texto_anterior = f"{format_with_dots(valor_anterior)}€"
    elif formato == "porcentaje":
        texto_actual = f"{valor_actual:.1f}%"
        texto_anterior = f"{valor_anterior:.1f}%"
    else:
        texto_actual = format_with_dots(valor_actual)
        texto_anterior = format_with_dots(valor_anterior)

    if not comparar:
        # Modo "solo dato" — no comparativa
        return html.Div([
            label_div,
            html.Div([
                html.Span(texto_actual, className="kpi-value kpi-value-neutral"),
            ], style={"display": "flex", "alignItems": "baseline",
                       "justifyContent": "center", "gap": "5px"}),
        ], className="kpi-card")

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


# Componente de loading
def loading_component():
    return html.Div([
        html.Div(className="loading-spinner"),
        html.Div("Cargando datos...", className="loading-text")
    ], className="loading-container")


def create_section_header(active_tab="cesiones"):
    """Crea el header con tabs de navegación horizontal."""
    tabs = [
        {"id": "entradas", "label": "Entradas", "href": "/estadio/entradas"},
        {"id": "asistencia", "label": "Asistencia", "href": "/estadio/asistencia"},
        {"id": "cesiones", "label": "Cesiones", "href": "/estadio/cesiones"},
    ]
    
    return html.Div([
        html.Div("ESTADIO ABANCA-RIAZOR", className="section-title"),
        html.Div([
            dcc.Link(
                tab["label"],
                href=tab["href"],
                className=f"section-tab {'active' if tab['id'] == active_tab else ''}"
            ) for tab in tabs
        ], className="section-tabs")
    ], className="section-header")


# Layout de la página
layout = html.Div([
    create_section_header("cesiones"),
    temporada_toggle(toggle_id="toggle-temp-cesiones",
                      store_id="temp-store-cesiones"),
    dcc.Loading(
        id="loading-cesiones",
        type="default",
        fullscreen=False,
        children=html.Div(id="content-cesiones", children=loading_component()),
        custom_spinner=loading_component(),
    )
])


# Callback que alterna el estado del toggle al hacer clic
@callback(
    Output("temp-store-cesiones", "data"),
    Output("toggle-temp-cesiones", "className"),
    Input("toggle-temp-cesiones", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_temporada_cesiones(n_clicks):
    if not n_clicks:
        return "actual", "season-toggle"
    activo = (n_clicks % 2 == 1)
    return ("anterior" if activo else "actual",
            "season-toggle active" if activo else "season-toggle")


def create_page_content(kpis, fig_recaudacion, fig1, fig2, fig3):
    """Crea el contenido completo de la página."""
    return html.Div([
        # KPIs
        html.Div(kpis, className="kpis-container"),
        
        # Gráficas
        html.Div([
            # Fila 1: Recaudación por cesiones por partido
            html.Div([
                html.Div([
                    html.H4("Recaudación por Cesiones por Partido"),
                    dcc.Graph(figure=fig_recaudacion, config={'displayModeBar': False})
                ], className="graph-card full-width"),
            ], className="graphs-row"),
            
            # Fila 2: Cesiones vendidas vs no vendidas por partido
            html.Div([
                html.Div([
                    html.H4("Cesiones Vendidas vs No Vendidas por Partido"),
                    dcc.Graph(figure=fig1, config={'displayModeBar': False})
                ], className="graph-card full-width"),
            ], className="graphs-row"),
            
            # Fila 3: Promedio por día y hora
            html.Div([
                html.Div([
                    html.H4("Promedio de Cesiones Vendidas por Día de la Semana"),
                    dcc.Graph(figure=fig2, config={'displayModeBar': False})
                ], className="graph-card small"),
                html.Div([
                    html.H4("Promedio de Cesiones Vendidas por Hora del Partido"),
                    dcc.Graph(figure=fig3, config={'displayModeBar': False})
                ], className="graph-card small"),
            ], className="graphs-row"),
        ], className="graphs-container"),
    ], className="page-content-container")


# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output("content-cesiones", "children"),
    Input("content-cesiones", "id"),
    Input("temp-store-cesiones", "data"),
)
def update_graphs(_, temp_seleccionada):
    """Actualiza todas las gráficas con datos pre-calculados.

    `temp_seleccionada` viene del toggle Temporada 24/25:
        'actual'   → temp 25/26 con KPIs comparados vs 24/25.
        'anterior' → temp 24/25 con KPIs sin comparativa.
    """
    df_all = get_data()
    temp = temp_seleccionada or 'actual'
    es_anterior = (temp == 'anterior')

    if df_all.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{"text": "No hay datos disponibles", "showarrow": False}]
        )
        return create_page_content([], empty_fig, empty_fig, empty_fig, empty_fig)

    df_partido = df_all[df_all['temporada'] == temp].sort_values('schedule')
    df_partido_ant = (df_all[df_all['temporada'] == 'anterior']
                       if not es_anterior else pd.DataFrame())

    if df_partido.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{"text": f"No hay datos para la temporada {('24/25' if es_anterior else '25/26')}",
                          "showarrow": False}]
        )
        return create_page_content([], empty_fig, empty_fig, empty_fig, empty_fig)

    # KPIs (sin comparativa cuando es_anterior)
    total_cesiones = df_partido['total_cesiones'].sum()
    total_vendidas = df_partido['vendidas'].sum()
    total_saldo = df_partido['saldo_total'].sum()
    rec_media = (total_saldo / total_vendidas) if total_vendidas > 0 else 0

    total_cesiones_ant = df_partido_ant['total_cesiones'].sum() if not df_partido_ant.empty else 0
    total_vendidas_ant = df_partido_ant['vendidas'].sum() if not df_partido_ant.empty else 0
    total_saldo_ant = df_partido_ant['saldo_total'].sum() if not df_partido_ant.empty else 0
    rec_media_ant = (total_saldo_ant / total_vendidas_ant) if total_vendidas_ant > 0 else 0

    comparar = not es_anterior
    kpis = html.Div([
        create_kpi_card(total_cesiones, total_cesiones_ant, "Total Cesiones Generadas",
                        tooltip="Nº total de abonos puestos a la venta por los abonados a través del sistema de cesiones.",
                        comparar=comparar),
        create_kpi_card(total_vendidas, total_vendidas_ant, "Cesiones Vendidas",
                        tooltip="Nº de cesiones que fueron efectivamente vendidas.",
                        comparar=comparar),
        create_kpi_card(rec_media, rec_media_ant, "Recaudación Media por Cesión", "euros",
                        tooltip="Importe medio obtenido por cada cesión vendida. Cálculo: Recaudación Total ÷ Cesiones Vendidas.",
                        comparar=comparar),
        create_kpi_card(total_saldo, total_saldo_ant, "Recaudación Total", "euros",
                        tooltip="Suma total de ingresos por venta de cesiones en todos los partidos.",
                        comparar=comparar),
    ], className="kpis-row")

    # Cargar desglose por sector para hovers (filtrado por temporada seleccionada)
    df_sector = get_pre_cesiones_sector()
    df_sector_actual = df_sector[df_sector['temporada'] == temp]
    gradas_orden = ['FONDO MARATHON', 'PREFERENCIA', 'FONDO PABELLON', 'TRIBUNA']
    
    def build_sector_hover(match_ids, metric, is_euros=False):
        """Construye lista de hover texts con desglose por grada para cada partido."""
        hovers = []
        for mid in match_ids:
            rows = df_sector_actual[df_sector_actual['id_partido'] == mid]
            lines = []
            for g in gradas_orden:
                row = rows[rows['grada'] == g]
                val = row[metric].values[0] if len(row) > 0 else 0
                if is_euros:
                    lines.append(f"{g}: {val:,.0f}\u20ac".replace(',', '.'))
                else:
                    lines.append(f"{g}: {val:,.0f}".replace(',', '.'))
            hovers.append('<br>'.join(lines))
        return hovers
    
    # Gráfica 1: Vendidas vs No Vendidas por partido (con escudos)
    rivales = df_partido['t2_name'].tolist()
    results = df_partido['result'].tolist()
    match_ids = df_partido['id_partido'].tolist()
    
    def format_number(val):
        return f"{val:,.0f}".replace(",", ".")
    
    hover_vendidas = build_sector_hover(match_ids, 'vendidas')
    hover_no_vendidas = build_sector_hover(match_ids, 'no_vendidas')
    
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        name='Vendidas (V)',
        x=list(range(len(rivales))),
        y=df_partido['vendidas'],
        marker_color='#2ecc71',
        text=[format_number(v) for v in df_partido['vendidas']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate='<b>Vendidas: %{y:,.0f}</b><br>%{customdata}<extra></extra>',
        customdata=hover_vendidas
    ))
    fig1.add_trace(go.Bar(
        name='No Vendidas (D)',
        x=list(range(len(rivales))),
        y=df_partido['no_vendidas'],
        marker_color='#e74c3c',
        text=[format_number(v) for v in df_partido['no_vendidas']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate='<b>No Vendidas: %{y:,.0f}</b><br>%{customdata}<extra></extra>',
        customdata=hover_no_vendidas
    ))
    
    escudos_images, result_shapes = create_escudos_with_result(rivales, results)
    
    max_y_fig1 = max(df_partido['vendidas'].max(), df_partido['no_vendidas'].max()) * 1.15 if len(df_partido) > 0 else 100
    fig1.update_layout(
        barmode='group',
        margin=dict(b=50, t=5, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
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
        yaxis=dict(showticklabels=False, range=[0, max_y_fig1])
    )
    
    # Gráfica 2: Promedio por día de la semana
    dias_traduccion = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    df_partido = df_partido.copy()
    df_partido['dia_semana_es'] = df_partido['dia_semana'].map(dias_traduccion)
    
    df_partido_dia = df_partido.groupby('dia_semana_es').agg({
        'vendidas': 'mean',
        'id_partido': 'count',
        't2_name': lambda x: list(x)
    }).reset_index()
    df_partido_dia.columns = ['dia_semana', 'promedio_vendidas', 'num_partidos', 'rivales']
    
    orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    df_partido_dia['dia_semana'] = pd.Categorical(df_partido_dia['dia_semana'], categories=orden_dias, ordered=True)
    df_partido_dia = df_partido_dia.sort_values('dia_semana').dropna()
    
    hover_dia = [
        f"<b>{d}</b><br>Promedio: {format_number(p)}<br>Partidos: {int(n)} ({', '.join(r)})"
        for d, p, n, r in zip(
            df_partido_dia['dia_semana'].astype(str),
            df_partido_dia['promedio_vendidas'],
            df_partido_dia['num_partidos'],
            df_partido_dia['rivales'],
        )
    ]
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_partido_dia['dia_semana'].astype(str),
        y=df_partido_dia['promedio_vendidas'],
        marker_color='#18395c',
        text=[f"{format_number(v)}" for v in df_partido_dia['promedio_vendidas']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertext=hover_dia,
        hoverinfo='text',
    ))
    max_y_dia = df_partido_dia['promedio_vendidas'].max() * 1.25
    fig2.update_layout(
        height=200,
        margin=dict(t=30, b=30, l=20, r=20),
        xaxis=dict(type='category', tickfont=dict(size=10, family='Montserrat', weight='bold')),
        yaxis=dict(showticklabels=False, range=[0, max_y_dia])
    )
    
    # Gráfica 3: Promedio por hora del partido
    df_hora_agg = df_partido.groupby('hora_exacta').agg({
        'vendidas': 'mean',
        'id_partido': 'count',
        't2_name': lambda x: list(x)
    }).reset_index()
    df_hora_agg.columns = ['hora', 'promedio_vendidas', 'num_partidos', 'rivales']
    
    hover_hora = [
        f"<b>Hora: {h}</b><br>Promedio: {format_number(p)}<br>Partidos: {int(n)} ({', '.join(r)})"
        for h, p, n, r in zip(
            df_hora_agg['hora'],
            df_hora_agg['promedio_vendidas'],
            df_hora_agg['num_partidos'],
            df_hora_agg['rivales'],
        )
    ]
    
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_hora_agg['hora'],
        y=df_hora_agg['promedio_vendidas'],
        marker_color='#18395c',
        text=[f"{format_number(v)}" for v in df_hora_agg['promedio_vendidas']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertext=hover_hora,
        hoverinfo='text',
    ))
    max_y_hora = df_hora_agg['promedio_vendidas'].max() * 1.25
    fig3.update_layout(
        height=200,
        margin=dict(t=30, b=30, l=20, r=20),
        xaxis=dict(tickfont=dict(size=10, family='Montserrat', weight='bold')),
        yaxis=dict(showticklabels=False, range=[0, max_y_hora])
    )
    
    # Gráfica Recaudación: Recaudación por cesiones por partido (con escudos)
    df_rec = get_pre_cesiones_recaudacion()
    df_rec['schedule'] = pd.to_datetime(df_rec['schedule'], errors='coerce')
    df_rec_actual = df_rec[df_rec['temporada'] == temp].sort_values('schedule')
    
    match_ids_rec = df_rec_actual['id_partido'].tolist()
    hover_rec = build_sector_hover(match_ids_rec, 'recaudacion', is_euros=True)
    
    fig_recaudacion = go.Figure()
    fig_recaudacion.add_trace(go.Bar(
        x=list(range(len(df_rec_actual))),
        y=df_rec_actual['rec_ces_vend'],
        marker_color='#f39c12',
        text=[format_number(v) + '€' for v in df_rec_actual['rec_ces_vend']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate='<b>Recaudación: %{y:,.0f}€</b><br>%{customdata}<extra></extra>',
        customdata=hover_rec
    ))
    
    rivales_rec = df_rec_actual['t2_name'].tolist()
    results_rec = df_rec_actual['result'].tolist()
    escudos_rec, result_shapes_rec = create_escudos_with_result(rivales_rec, results_rec)
    
    max_y_rec = df_rec_actual['rec_ces_vend'].max() * 1.15 if len(df_rec_actual) > 0 else 100
    fig_recaudacion.update_layout(
        margin=dict(b=50, t=5, l=20, r=20),
        height=350,
        images=escudos_rec,
        shapes=result_shapes_rec,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(rivales_rec))),
            ticktext=['' for _ in rivales_rec],
            showticklabels=False,
            range=[-0.5, len(rivales_rec) - 0.5] if len(rivales_rec) > 0 else [0, 1]
        ),
        yaxis=dict(showticklabels=False, range=[0, max_y_rec])
    )
    
    return create_page_content(kpis, fig_recaudacion, fig1, fig2, fig3)
