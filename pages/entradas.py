"""
Página de Entradas - Estadio Abanca-Riazor
==========================================
Análisis de venta de entradas por partido
"""

import dash
from dash import html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date
from database import get_pre_entradas_partido, get_pre_entradas_sector

dash.register_page(__name__, path="/estadio/entradas", name="Entradas")

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
}


def get_escudo_path(team_name):
    """Obtiene la ruta del escudo para un equipo."""
    escudo_file = ESCUDOS_MAP.get(team_name)
    if escudo_file:
        return f"/assets/Escudos/{escudo_file}"
    return None


def get_data():
    """Obtiene datos pre-calculados de entradas por partido."""
    try:
        df = get_pre_entradas_partido()
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
            return '#2ecc71'  # Verde - victoria
        elif home < away:
            return '#e74c3c'  # Rojo - derrota
        else:
            return '#f39c12'  # Amarillo - empate
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

def create_kpi_card(valor_actual, valor_anterior, label, formato="numero"):
    """Crea una tarjeta KPI con comparativa y % de diferencia."""
    if formato == "euros":
        texto_actual = f"{format_with_dots(valor_actual)}€"
        texto_anterior = f"{format_with_dots(valor_anterior)}€"
    elif formato == "entradas":
        texto_actual = f"{format_with_dots(valor_actual)} entradas"
        texto_anterior = f"{format_with_dots(valor_anterior)} entradas"
    else:
        texto_actual = format_with_dots(valor_actual)
        texto_anterior = format_with_dots(valor_anterior)
    
    # Calcular % de diferencia
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
        html.Div(label, className="kpi-label-top"),
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


def create_section_header(active_tab="entradas"):
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
    create_section_header("entradas"),
    dcc.Loading(
        id="loading-entradas",
        type="default",
        fullscreen=False,
        children=html.Div(id="content-entradas", children=loading_component()),
        custom_spinner=loading_component(),
    )
])


def create_page_content(kpis, fig1, fig2, fig3, fig4):
    """Crea el contenido completo de la página."""
    return html.Div([
        # KPIs
        html.Div(kpis, className="kpis-container"),
        
        # Gráficas
        html.Div([
            # Fila 1: Recaudación por partido
            html.Div([
                html.Div([
                    html.H4("Recaudación por Partido"),
                    dcc.Graph(figure=fig4, config={'displayModeBar': False})
                ], className="graph-card full-width"),
            ], className="graphs-row"),
            
            # Fila 2: Entradas vendidas vs no vendidas por partido
            html.Div([
                html.Div([
                    html.H4("Entradas Vendidas vs No Vendidas por Partido"),
                    dcc.Graph(figure=fig1, config={'displayModeBar': False})
                ], className="graph-card full-width"),
            ], className="graphs-row"),
            
            # Fila 3: Promedio por día y hora
            html.Div([
                html.Div([
                    html.H4("Promedio de Entradas Vendidas por Día de la Semana"),
                    dcc.Graph(figure=fig2, config={'displayModeBar': False})
                ], className="graph-card small"),
                html.Div([
                    html.H4("Promedio de Entradas Vendidas por Franja Horaria"),
                    dcc.Graph(figure=fig3, config={'displayModeBar': False})
                ], className="graph-card small"),
            ], className="graphs-row"),
        ], className="graphs-container"),
    ], className="page-content-container")


# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output("content-entradas", "children"),
    Input("content-entradas", "id")
)
def update_page(_):
    """Actualiza todas las gráficas con datos pre-calculados."""
    df_all = get_data()
    
    if df_all.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{"text": "No hay datos disponibles", "showarrow": False}]
        )
        return create_page_content([], empty_fig, empty_fig, empty_fig, empty_fig)
    
    # Separar temporadas (ya pre-filtradas)
    df_partido = df_all[df_all['temporada'] == 'actual'].sort_values('schedule')
    df_partido_ant = df_all[df_all['temporada'] == 'anterior']
    
    if df_partido.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{"text": "No hay datos para la temporada actual", "showarrow": False}]
        )
        return create_page_content([], empty_fig, empty_fig, empty_fig, empty_fig)
    
    # KPIs actuales
    total_vendidas = df_partido['n_publico'].sum()
    total_recaudacion = df_partido['recaudacion'].sum()
    num_partidos = len(df_partido)
    promedio_vendidas = total_vendidas / num_partidos if num_partidos > 0 else 0
    recaudacion_por_partido = total_recaudacion / num_partidos if num_partidos > 0 else 0
    
    # KPIs temporada anterior
    total_vendidas_ant = df_partido_ant['n_publico'].sum()
    total_recaudacion_ant = df_partido_ant['recaudacion'].sum()
    num_partidos_ant = len(df_partido_ant)
    promedio_vendidas_ant = total_vendidas_ant / num_partidos_ant if num_partidos_ant > 0 else 0
    recaudacion_por_partido_ant = total_recaudacion_ant / num_partidos_ant if num_partidos_ant > 0 else 0
    
    kpis = html.Div([
        create_kpi_card(total_vendidas, total_vendidas_ant, "Total Entradas Vendidas", "entradas"),
        create_kpi_card(promedio_vendidas, promedio_vendidas_ant, "Entradas por Partido", "entradas"),
        create_kpi_card(total_recaudacion, total_recaudacion_ant, "Recaudación Total", "euros"),
        create_kpi_card(recaudacion_por_partido, recaudacion_por_partido_ant, "Recaudación por Partido", "euros"),
    ], className="kpis-row")
    
    # Cargar desglose por sector para hovers
    df_sector = get_pre_entradas_sector()
    df_sector_actual = df_sector[df_sector['temporada'] == 'actual']
    gradas_orden = ['FONDO MARATHON', 'PREFERENCIA', 'FONDO PABELLON', 'TRIBUNA']
    
    def build_sector_hover(match_ids, metric):
        """Construye lista de hover texts con desglose por grada para cada partido."""
        hovers = []
        for mid in match_ids:
            rows = df_sector_actual[df_sector_actual['id_partido'] == mid]
            lines = []
            for g in gradas_orden:
                row = rows[rows['grada'] == g]
                val = row[metric].values[0] if len(row) > 0 else 0
                if metric == 'recaudacion':
                    lines.append(f"{g}: {val:,.0f}€".replace(',', '.'))
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
        name='Vendidas',
        x=list(range(len(rivales))),
        y=df_partido['n_publico'],
        marker_color='#2ecc71',
        text=[format_number(v) for v in df_partido['n_publico']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate='<b>Vendidas: %{y:,.0f}</b><br>%{customdata}<extra></extra>',
        customdata=hover_vendidas
    ))
    fig1.add_trace(go.Bar(
        name='No Vendidas',
        x=list(range(len(rivales))),
        y=df_partido['norm_no_vend'],
        marker_color='#e74c3c',
        text=[format_number(v) for v in df_partido['norm_no_vend']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate='<b>No Vendidas: %{y:,.0f}</b><br>%{customdata}<extra></extra>',
        customdata=hover_no_vendidas
    ))
    
    escudos_images, result_shapes = create_escudos_with_result(rivales, results)
    
    max_y_fig1 = max(df_partido['n_publico'].max(), df_partido['norm_no_vend'].max()) * 1.15 if len(df_partido) > 0 else 100
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
        yaxis=dict(showticklabels=False, range=[0, max_y_fig1]),
        separators=',.',
    )
    
    # Gráfica 2: Promedio por día de la semana
    dias_traduccion = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    df_partido = df_partido.copy()
    df_partido['dia_semana_es'] = df_partido['dia_semana'].map(dias_traduccion)
    
    df_partido_dia = df_partido.groupby('dia_semana_es').agg({
        'n_publico': 'mean',
        'id_partido': 'count',
        't2_name': lambda x: list(x)
    }).reset_index()
    df_partido_dia.columns = ['dia_semana', 'promedio_vendidas', 'num_partidos', 'rivales']
    
    orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    df_partido_dia['dia_semana'] = pd.Categorical(df_partido_dia['dia_semana'], categories=orden_dias, ordered=True)
    df_partido_dia = df_partido_dia.sort_values('dia_semana').dropna()
    
    hover_dia = ["<br>".join(r) for r in df_partido_dia['rivales'].tolist()]
    
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_partido_dia['dia_semana'].astype(str),
        y=df_partido_dia['promedio_vendidas'],
        marker_color='#3498db',
        text=[f"{format_number(v)}" for v in df_partido_dia['promedio_vendidas']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate='<b>Rivales:</b><br>%{customdata}<extra></extra>',
        customdata=hover_dia
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
        'n_publico': 'mean',
        'id_partido': 'count',
        't2_name': lambda x: list(x)
    }).reset_index()
    df_hora_agg.columns = ['hora', 'promedio_vendidas', 'num_partidos', 'rivales']
    
    hover_hora = ["<br>".join(r) for r in df_hora_agg['rivales'].tolist()]
    
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_hora_agg['hora'],
        y=df_hora_agg['promedio_vendidas'],
        marker_color='#9b59b6',
        text=[f"{format_number(v)}" for v in df_hora_agg['promedio_vendidas']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate='<b>Rivales:</b><br>%{customdata}<extra></extra>',
        customdata=hover_hora
    ))
    max_y_hora = df_hora_agg['promedio_vendidas'].max() * 1.25
    fig3.update_layout(
        height=200,
        margin=dict(t=30, b=30, l=20, r=20),
        xaxis=dict(tickfont=dict(size=10, family='Montserrat', weight='bold')),
        yaxis=dict(showticklabels=False, range=[0, max_y_hora])
    )
    
    # Gráfica 4: Recaudación por partido (con escudos)
    hover_recaudacion = build_sector_hover(match_ids, 'recaudacion')
    
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=list(range(len(rivales))),
        y=df_partido['recaudacion'],
        marker_color='#f39c12',
        text=[format_number(v) + '€' for v in df_partido['recaudacion']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate='<b>Recaudación: %{y:,.0f}€</b><br>%{customdata}<extra></extra>',
        customdata=hover_recaudacion
    ))
    
    max_y_fig4 = df_partido['recaudacion'].max() * 1.15 if len(df_partido) > 0 else 100
    fig4.update_layout(
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
        yaxis=dict(showticklabels=False, range=[0, max_y_fig4])
    )
    
    return create_page_content(kpis, fig1, fig2, fig3, fig4)
