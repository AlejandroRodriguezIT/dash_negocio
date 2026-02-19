"""
Página de Asistencia - Estadio Abanca-Riazor
=============================================
Análisis de asistencia de abonados a partidos
"""

import dash
from dash import html, dcc, callback, Output, Input
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import (
    get_pre_asistencia_kpis, get_pre_asistencia_sector,
    get_pre_asistencia_consecutiva, get_pre_asistencia_partido,
    get_pre_asistencia_edad
)

dash.register_page(__name__, path="/estadio/asistencia", name="Asistencia")

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


def calcular_edad(birthdate):
    """Calcula la edad a partir de la fecha de nacimiento."""
    if pd.isna(birthdate):
        return None
    try:
        birth = pd.to_datetime(birthdate)
        today = datetime.now()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except:
        return None


def clasificar_edad(edad):
    """Clasifica la edad en intervalos."""
    if pd.isna(edad):
        return 'Sin datos'
    if edad < 16:
        return '<16 años'
    elif edad <= 30:
        return '16-30 años'
    elif edad <= 45:
        return '31-45 años'
    elif edad <= 60:
        return '46-60 años'
    else:
        return '>60 años'


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


def create_kpi_abonados(promedio_actual, pct_actual, promedio_anterior, pct_anterior):
    """Tarjeta KPI de Abonados por Partido con % del total integrado."""
    if promedio_anterior > 0:
        pct_diff = ((promedio_actual - promedio_anterior) / promedio_anterior) * 100
        if pct_diff >= 0:
            pct_text = f"+{pct_diff:.1f}%"
            color_class = "kpi-value-positive"
            color_css = "var(--success-green)"
        else:
            pct_text = f"{pct_diff:.1f}%"
            color_class = "kpi-value-negative"
            color_css = "var(--danger-red)"
    else:
        pct_text = "N/A"
        color_class = "kpi-value-positive"
        color_css = "var(--success-green)"
    
    return html.Div([
        html.Div("Abonados por Partido (% del total)", className="kpi-label-top"),
        html.Div([
            html.Span(format_with_dots(promedio_actual), className=f"kpi-value {color_class}"),
            html.Span(f" ({pct_actual:.1f}%)", style={"fontSize": "0.85rem", "fontWeight": "600", "color": color_css}),
            html.Span(f" ({pct_text})", className=f"kpi-pct-diff {color_class}")
        ], style={"display": "flex", "alignItems": "baseline", "justifyContent": "center", "gap": "4px"}),
        html.Div(f"Temp. 24/25: {format_with_dots(promedio_anterior)} ({pct_anterior:.1f}%)", className="kpi-previous"),
    ], className="kpi-card")


def create_kpi_sexo(df_sexo, total_abonados):
    """Tarjeta KPI con desglose por sexo."""
    male_count = df_sexo[df_sexo['gender'] == 'MALE']['total'].sum() if 'MALE' in df_sexo['gender'].values else 0
    female_count = df_sexo[df_sexo['gender'] == 'FEMALE']['total'].sum() if 'FEMALE' in df_sexo['gender'].values else 0
    male_pct = (male_count / total_abonados * 100) if total_abonados > 0 else 0
    female_pct = (female_count / total_abonados * 100) if total_abonados > 0 else 0
    
    return html.Div([
        html.Div("Sexo de los Abonados", className="kpi-label-top"),
        html.Div([
            html.Div([
                html.Span(format_with_dots(male_count), style={"fontSize": "1.2rem", "fontWeight": "700", "color": "#2c5282"}),
                html.Span(f" ({male_pct:.1f}%)", style={"fontSize": "0.8rem", "fontWeight": "600", "color": "#2c5282"}),
                html.Div("Masculino", style={"fontSize": "0.65rem", "color": "#666", "marginTop": "2px"}),
            ], style={"display": "inline-block", "textAlign": "center", "marginRight": "15px"}),
            html.Div([
                html.Span(format_with_dots(female_count), style={"fontSize": "1.2rem", "fontWeight": "700", "color": "#FFB5C0"}),
                html.Span(f" ({female_pct:.1f}%)", style={"fontSize": "0.8rem", "fontWeight": "600", "color": "#FFB5C0"}),
                html.Div("Femenino", style={"fontSize": "0.65rem", "color": "#666", "marginTop": "2px"}),
            ], style={"display": "inline-block", "textAlign": "center"}),
        ], style={"display": "flex", "justifyContent": "center", "gap": "10px"}),
    ], className="kpi-card")


def create_kpi_edad(edad_promedio):
    """Tarjeta KPI de edad promedio (solo informativo, sin comparativa)."""
    return html.Div([
        html.Div("Edad Promedio", className="kpi-label-top"),
        html.Div(
            f"{edad_promedio:.1f} años",
            className="kpi-value",
            style={"color": "var(--primary-blue)"}
        ),
    ], className="kpi-card")


def create_kpi_tardios(promedio_actual, pct_tarde, promedio_anterior, pct_tarde_anterior):
    """Tarjeta KPI de Abonados Tardíos (lógica inversa: menor es mejor)."""
    if promedio_anterior > 0:
        pct_diff = ((promedio_actual - promedio_anterior) / promedio_anterior) * 100
        if pct_diff <= 0:
            pct_text = f"{pct_diff:.1f}%"
            color_class = "kpi-value-positive"
            color_css = "var(--success-green)"
        else:
            pct_text = f"+{pct_diff:.1f}%"
            color_class = "kpi-value-negative"
            color_css = "var(--danger-red)"
    else:
        pct_text = "N/A"
        color_class = "kpi-value-positive"
        color_css = "var(--success-green)"
    
    return html.Div([
        html.Div("Abonados Tardíos por partido", className="kpi-label-top"),
        html.Div([
            html.Span(format_with_dots(promedio_actual), className=f"kpi-value {color_class}"),
            html.Span(f" ({pct_text})", className=f"kpi-pct-diff {color_class}")
        ], style={"display": "flex", "alignItems": "baseline", "justifyContent": "center", "gap": "4px"}),
        html.Div(f"Temp. 24/25: {format_with_dots(promedio_anterior)}", className="kpi-previous"),
    ], className="kpi-card")


def loading_component():
    return html.Div([
        html.Div(className="loading-spinner"),
        html.Div("Cargando datos...", className="loading-text")
    ], className="loading-container")


def create_section_header(active_tab="asistencia"):
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


layout = html.Div([
    create_section_header("asistencia"),
    dcc.Loading(
        id="loading-asistencia",
        type="default",
        fullscreen=False,
        children=html.Div(id="content-asistencia", children=loading_component()),
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
            # Fila 1: Evolutivo de Asistencia
            html.Div([
                html.Div([
                    html.H4("Evolutivo de Asistencia ABANCA - Riazor"),
                    dcc.Graph(figure=fig3, config={'displayModeBar': False})
                ], className="graph-card full-width"),
            ], className="graphs-row"),
            
            # Fila 2: Asistencia por grada y por edad
            html.Div([
                html.Div([
                    html.H4("Promedio de Abonados Asistentes por Grada"),
                    dcc.Graph(figure=fig1, config={'displayModeBar': False})
                ], className="graph-card small"),
                html.Div([
                    html.H4("Promedio de Abonados Asistentes por Edad"),
                    dcc.Graph(figure=fig4, config={'displayModeBar': False})
                ], className="graph-card small"),
            ], className="graphs-row"),
            
            # Fila 3: Abonados consecutivos por jornada
            html.Div([
                html.Div([
                    html.H4("Número de Abonados con Asistencia Consecutiva por Jornada"),
                    dcc.Graph(figure=fig2, config={'displayModeBar': False})
                ], className="graph-card full-width"),
            ], className="graphs-row"),
        ], className="graphs-container"),
    ], className="page-content-container")


@callback(
    Output("content-asistencia", "children"),
    Input("content-asistencia", "id")
)
def update_page(_):
    """Actualiza todas las gráficas con datos pre-calculados."""
    try:
        # Obtener datos pre-calculados (consultas simples, sin JOINs pesados)
        df_kpis = get_pre_asistencia_kpis()
        df_sector = get_pre_asistencia_sector()
        df_consecutiva = get_pre_asistencia_consecutiva()
        df_partido = get_pre_asistencia_partido()
        df_edad = get_pre_asistencia_edad()
        
        if df_kpis.empty:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                annotations=[{"text": "No hay datos disponibles. Ejecuta sync_data.py primero.", "showarrow": False}]
            )
            return create_page_content([], empty_fig, empty_fig, empty_fig, empty_fig)
        
        # =====================================================================
        # KPIs (ya pre-calculados)
        # =====================================================================
        kpi_actual = df_kpis[df_kpis['temporada'] == 'actual'].iloc[0]
        kpi_anterior = df_kpis[df_kpis['temporada'] == 'anterior'].iloc[0]
        
        # Crear KPI de sexo manualmente desde datos pre-calculados
        df_sexo_kpi = html.Div([
            html.Div("Sexo de los Abonados", className="kpi-label-top"),
            html.Div([
                html.Div([
                    html.Span(format_with_dots(kpi_actual['male_count']), style={"fontSize": "1.2rem", "fontWeight": "700", "color": "#2c5282"}),
                    html.Span(f" ({kpi_actual['male_pct']:.1f}%)", style={"fontSize": "0.8rem", "fontWeight": "600", "color": "#2c5282"}),
                    html.Div("Masculino", style={"fontSize": "0.65rem", "color": "#666", "marginTop": "2px"}),
                ], style={"display": "inline-block", "textAlign": "center", "marginRight": "15px"}),
                html.Div([
                    html.Span(format_with_dots(kpi_actual['female_count']), style={"fontSize": "1.2rem", "fontWeight": "700", "color": "#FFB5C0"}),
                    html.Span(f" ({kpi_actual['female_pct']:.1f}%)", style={"fontSize": "0.8rem", "fontWeight": "600", "color": "#FFB5C0"}),
                    html.Div("Femenino", style={"fontSize": "0.65rem", "color": "#666", "marginTop": "2px"}),
                ], style={"display": "inline-block", "textAlign": "center"}),
            ], style={"display": "flex", "justifyContent": "center", "gap": "10px"}),
        ], className="kpi-card")
        
        kpis = html.Div([
            create_kpi_abonados(
                kpi_actual['promedio_asistentes'], kpi_actual['pct_asistencia'],
                kpi_anterior['promedio_asistentes'], kpi_anterior['pct_asistencia']
            ),
            df_sexo_kpi,
            create_kpi_edad(kpi_actual['edad_promedio']),
            create_kpi_tardios(
                kpi_actual['promedio_tarde'], kpi_actual['pct_tarde'],
                kpi_anterior['promedio_tarde'], kpi_anterior['pct_tarde']
            ),
        ], className="kpis-row")
        
        # =====================================================================
        # GRÁFICA 1: % Promedio de Asistencia por Grada (pre-calculado)
        # =====================================================================
        promedio_sector = df_sector.sort_values('pct_asistencia', ascending=False)
        
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=promedio_sector['sector'],
            y=promedio_sector['pct_asistencia'],
            marker_color='#18395c',
            text=[f"{format_with_dots(a)}<br>{v:.1f}%" for a, v in zip(promedio_sector['asistentes'], promedio_sector['pct_asistencia'])],
            textposition='outside',
            textfont=dict(color='#333', size=11, family='Montserrat', weight='bold')
        ))
        max_y_grada = promedio_sector['pct_asistencia'].max() * 1.3 if len(promedio_sector) > 0 else 100
        fig1.update_layout(
            height=280,
            margin=dict(t=10, b=40, l=10, r=10),
            xaxis=dict(tickfont=dict(size=10, family='Montserrat', weight='bold')),
            yaxis=dict(visible=False, range=[0, max_y_grada])
        )
        
        # =====================================================================
        # GRÁFICA 2: Abonados con Asistencia Consecutiva (pre-calculado)
        # =====================================================================
        rivales_list = df_consecutiva['t2_name'].tolist()
        results_list = df_consecutiva['result'].tolist()
        abonados_consecutivos = df_consecutiva['abonados_consecutivos'].tolist()
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=list(range(len(rivales_list))),
            y=abonados_consecutivos,
            marker_color='#18395c',
            text=[format_with_dots(v) for v in abonados_consecutivos],
            textposition='outside',
            textfont=dict(color='#333', size=10, family='Montserrat', weight='bold')
        ))
        
        escudos_images_f2, result_shapes_f2 = create_escudos_with_result(rivales_list, results_list, y_pos=-0.12, sizex=0.55, sizey=0.10)
        
        max_y = max(abonados_consecutivos) * 1.2 if abonados_consecutivos else 100
        fig2.update_layout(
            height=400,
            margin=dict(b=50, t=10, l=40, r=20),
            images=escudos_images_f2,
            shapes=result_shapes_f2,
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(len(rivales_list))),
                ticktext=['' for _ in rivales_list],
                showticklabels=False,
                range=[-0.5, len(rivales_list) - 0.5] if rivales_list else [0, 1]
            ),
            yaxis=dict(title='Abonados Consecutivos', range=[0, max_y])
        )
        
        # =====================================================================
        # GRÁFICA 3: Espectadores Totales vs Abonados (pre-calculado)
        # =====================================================================
        datos_grafica = df_partido.sort_values('schedule')
        rivales_g3 = datos_grafica['t2_name'].tolist()
        results_g3 = datos_grafica['result'].tolist()
        
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=list(range(len(rivales_g3))),
            y=datos_grafica['total_espectadores'],
            mode='lines+markers+text',
            name='Espectadores Totales',
            line=dict(color='#3498db', width=2),
            marker=dict(size=8),
            text=[format_with_dots(v) for v in datos_grafica['total_espectadores']],
            textposition='top center',
            textfont=dict(size=9, color='#3498db', weight='bold')
        ))
        fig3.add_trace(go.Scatter(
            x=list(range(len(rivales_g3))),
            y=datos_grafica['abonados_asistentes'],
            mode='lines+markers+text',
            name='Abonados Asistentes',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=8),
            text=[format_with_dots(v) for v in datos_grafica['abonados_asistentes']],
            textposition='bottom center',
            textfont=dict(size=9, color='#e74c3c', weight='bold')
        ))
        
        escudos_g3, result_shapes_g3 = create_escudos_with_result(rivales_g3, results_g3)
        
        fig3.update_layout(
            height=400,
            margin=dict(b=50, t=20, l=40, r=20),
            images=escudos_g3,
            shapes=result_shapes_g3,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(len(rivales_g3))),
                ticktext=['' for _ in rivales_g3],
                showticklabels=False,
                range=[-0.5, len(rivales_g3) - 0.5] if rivales_g3 else [0, 1]
            ),
            yaxis=dict(title='Personas')
        )
        
        # =====================================================================
        # GRÁFICA 4: Promedio de Abonados Asistentes por Edad (pre-calculado)
        # =====================================================================
        promedio_edad = df_edad
        
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=promedio_edad['grupo_edad'],
            y=promedio_edad['asistentes'],
            marker_color='#18395c',
            text=[f"{format_with_dots(v)}<br>({p:.1f}%)" for v, p in zip(promedio_edad['asistentes'], promedio_edad['pct'])],
            textposition='outside',
            textfont=dict(color='#333', size=10, family='Montserrat', weight='bold')
        ))
        max_y_edad = promedio_edad['asistentes'].max() * 1.35 if len(promedio_edad) > 0 else 100
        fig4.update_layout(
            height=280,
            margin=dict(t=10, b=40, l=10, r=10),
            xaxis=dict(tickfont=dict(size=10, family='Montserrat', weight='bold')),
            yaxis=dict(visible=False, range=[0, max_y_edad])
        )
        
        return create_page_content(kpis, fig1, fig2, fig3, fig4)
        
    except Exception as e:
        print(f"Error en asistencia: {e}")
        import traceback
        traceback.print_exc()
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{"text": f"Error: {str(e)}", "showarrow": False}]
        )
        return create_page_content([], empty_fig, empty_fig, empty_fig, empty_fig)
