"""
Página Museo RCD
=================
Dashboard de ventas del Museo + Tours del RC Deportivo.
"""

import dash
from dash import html, dcc, callback, Output, Input
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from database import (
    get_museo_kpis, get_museo_diario, get_museo_producto,
    get_museo_horario, get_museo_dia_semana, get_museo_canal,
    get_museo_metodo_pago, get_museo_heatmap, get_museo_partidos_local,
)

dash.register_page(__name__, path="/museo", name="Museo RCD")


# =============================================================================
# HELPERS
# =============================================================================

FONT = "Montserrat"
PRIMARY = "#18395c"
SECONDARY = "#3498db"
ACCENT = "#f39c12"
GREEN = "#2ecc71"
LIGHT_BG = "#f5f5f5"

ESCUDOS_MAP = {
    'Albacete': 'Albacete BP.png',
    'Albacete BP': 'Albacete BP.png',
    'Burgos': 'Burgos CF.png',
    'Burgos CF': 'Burgos CF.png',
    'Castellón': 'CD Castellón.png',
    'CD Castellón': 'CD Castellón.png',
    'Mirandés': 'CD Mirandés.png',
    'CD Mirandés': 'CD Mirandés.png',
    'Ceuta': 'Ceuta.png',
    'AD Ceuta FC': 'Ceuta.png',
    'Cultural Leonesa': 'Cultural.png',
    'Cádiz': 'Cádiz CF.png',
    'Cádiz CF': 'Cádiz CF.png',
    'Córdoba': 'Córdoba CF.png',
    'Córdoba CF': 'Córdoba CF.png',
    'Andorra': 'FC Andorra.png',
    'FC Andorra': 'FC Andorra.png',
    'Granada': 'Granada CF.png',
    'Granada CF': 'Granada CF.png',
    'Mallorca': 'Mallorca.png',
    'Málaga': 'Málaga CF.png',
    'Málaga CF': 'Málaga CF.png',
    'RC Deportivo': 'RC Deportivo.png',
    'Deportivo de La Coruña': 'RC Deportivo.png',
    'Racing': 'Real Racing Club.png',
    'Real Racing Club': 'Real Racing Club.png',
    'Real Sociedad B': 'Real Sociedad B.png',
    'Sporting': 'Real Sporting.png',
    'Sporting de Gijón': 'Real Sporting.png',
    'Valladolid': 'Real Valladolid CF.png',
    'Real Valladolid CF': 'Real Valladolid CF.png',
    'Zaragoza': 'Real Zaragoza.png',
    'Real Zaragoza': 'Real Zaragoza.png',
    'Eibar': 'SD Eibar.png',
    'SD Eibar': 'SD Eibar.png',
    'Huesca': 'SD Huesca.png',
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


def fmt(val):
    """Formatea número con separador de miles (punto)."""
    try:
        return f"{val:,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return str(val)


def fmt_eur(val):
    """Formatea número como euros."""
    return f"{fmt(val)}€"


def _kpi_tooltip(text):
    if not text:
        return None
    return html.Div([
        html.Span("?", className="kpi-tooltip-icon"),
        html.Div(text, className="kpi-tooltip-box"),
    ], className="kpi-tooltip-wrapper")


def create_kpi_simple(valor, label, formato="numero", tooltip=None):
    """KPI card estilo plataforma."""
    if formato == "euros":
        texto = fmt_eur(valor)
    elif formato == "decimal":
        texto = f"{valor:.2f}".replace(",", ".")
    else:
        texto = fmt(valor)
    label_children = [label]
    if tooltip:
        label_children.append(_kpi_tooltip(tooltip))
    label_div = html.Div(label_children, className="kpi-label-top",
                         style={"whiteSpace": "nowrap", "display": "flex",
                                "alignItems": "center", "justifyContent": "center",
                                "gap": "5px"})
    return html.Div([
        label_div,
        html.Div(texto, className="kpi-value kpi-value-positive",
                 style={"textAlign": "center"}),
    ], className="kpi-card")


def loading_component():
    return html.Div([
        html.Div(className="loading-spinner"),
        html.Div("Cargando datos...", className="loading-text")
    ], className="loading-container")


# =============================================================================
# LAYOUT
# =============================================================================

layout = html.Div([
    html.Div([
        html.Div("MUSEO RCD", className="section-title"),
    ], className="section-header"),
    dcc.Loading(
        id="loading-museo",
        type="default",
        fullscreen=False,
        children=html.Div(id="content-museo", children=loading_component()),
        custom_spinner=loading_component(),
    )
])


# =============================================================================
# CHART BUILDERS
# =============================================================================

def build_fig_evolucion_diaria(df_diario, df_partidos):
    """Línea de ingresos diarios con líneas verticales y escudos en días de partido.

    El eje X es **categórico** (`type='category'`), de modo que cada día con
    datos ocupa el mismo ancho horizontal en la gráfica, independientemente de
    los saltos temporales (días cerrados, vacaciones, etc.). Esto garantiza
    que los escudos y las líneas verticales de día de partido aparezcan
    siempre alineados con su día correspondiente y que la densidad visual sea
    uniforme a lo largo del eje.
    """
    df = df_diario.copy()
    df['fecha'] = pd.to_datetime(df['fecha'])
    daily = df.groupby('fecha').agg(
        ingresos=('ingresos_netos', 'sum'),
    ).reset_index().sort_values('fecha').reset_index(drop=True)

    # Categorías del eje X: string ISO 'YYYY-MM-DD' (orden lexicográfico = orden cronológico).
    daily['fecha_cat']  = daily['fecha'].dt.strftime('%Y-%m-%d')
    daily['fecha_disp'] = daily['fecha'].dt.strftime('%d/%m')
    daily['fecha_full'] = daily['fecha'].dt.strftime('%d/%m/%Y')

    max_y1 = daily['ingresos'].max() * 1.35 if not daily.empty else 100

    fig = go.Figure()

    # Línea ingresos (única serie de la gráfica)
    fig.add_trace(go.Scatter(
        x=daily['fecha_cat'], y=daily['ingresos'],
        mode='lines+markers',
        name='Ingresos (€)',
        line=dict(color=PRIMARY, width=2.5),
        marker=dict(size=4),
        text=[fmt_eur(v) for v in daily['ingresos']],
        customdata=daily['fecha_full'],
        hovertemplate='<b>%{customdata}</b><br>Ingresos: %{text}<extra></extra>',
    ))

    # Líneas verticales discontinuas y escudos en los días de partido.
    # Con eje categórico, las vlines deben implementarse como shapes (no add_vline,
    # que requiere ejes numéricos/temporales). El xref='x' espera la categoría
    # exacta (ISO 'YYYY-MM-DD') para alinearse con el día correcto.
    images = []
    shapes = []
    annotations = []
    if not df_partidos.empty:
        df_p = df_partidos.copy()
        df_p['fecha'] = pd.to_datetime(df_p['fecha'])
        df_p['fecha_cat'] = df_p['fecha'].dt.strftime('%Y-%m-%d')
        cat_set = set(daily['fecha_cat'])
        for _, row in df_p.iterrows():
            x_cat = row['fecha_cat']
            if x_cat not in cat_set:
                # El día del partido no tiene fila en df_diario (Museo cerrado);
                # saltamos para evitar romper el alineamiento del eje categórico.
                continue
            # Línea vertical de día de partido (shape, no add_vline)
            shapes.append(dict(
                type='line',
                xref='x', yref='paper',
                x0=x_cat, x1=x_cat,
                y0=0, y1=1,
                line=dict(color=ACCENT, width=1.5, dash='dash'),
                opacity=0.6,
                layer='below',
            ))
            # Escudo del rival sobre la línea
            escudo_path = get_escudo_path(row['rival'])
            if escudo_path:
                images.append(dict(
                    source=escudo_path,
                    xref='x', yref='y',
                    x=x_cat,
                    y=max_y1 * 0.98,
                    sizex=6,  # ~6 categorías de ancho con eje categórico
                    sizey=max_y1 * 0.18,
                    xanchor='center', yanchor='top',
                    layer='above',
                ))
            else:
                annotations.append(dict(
                    x=x_cat, y=max_y1 * 0.99,
                    text=f"<b>{row['rival']}</b>",
                    showarrow=False,
                    font=dict(size=8, family=FONT, color=ACCENT),
                    textangle=-45, yref='y',
                ))

    # Mostrar solo ~15 ticks repartidos a lo largo del eje para no saturar
    # cuando hay muchos días de datos (Sep–May ≈ 240 categorías).
    n_dates = len(daily)
    step = max(1, n_dates // 15) if n_dates > 30 else 1
    tickvals = daily['fecha_cat'].iloc[::step].tolist()
    ticktext = daily['fecha_disp'].iloc[::step].tolist()

    fig.update_layout(
        height=420,
        margin=dict(t=30, b=40, l=50, r=20),
        images=images,
        shapes=shapes,
        annotations=annotations,
        xaxis=dict(
            type='category',
            tickfont=dict(size=9, family=FONT),
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=-45,
        ),
        yaxis=dict(
            title=dict(text='Ingresos (€)', font=dict(size=10, family=FONT, color=PRIMARY)),
            tickfont=dict(size=9, family=FONT, color=PRIMARY),
            range=[0, max_y1],
            showgrid=True, gridcolor='rgba(0,0,0,0.05)',
        ),
        showlegend=False,
        plot_bgcolor='white',
    )
    return fig


def build_fig_producto(df_producto):
    """Donut: distribución por tipo de tour."""
    colores = {'Tour Guiado': PRIMARY, 'Tour Libre': SECONDARY}
    fig = go.Figure()
    total = df_producto['ingresos_netos'].sum()
    pcts = (df_producto['ingresos_netos'] / total * 100).round(1) if total > 0 else [0] * len(df_producto)
    labels_txt = [
        f"<b>{lbl}</b><br>{pct:.1f}%<br>{fmt_eur(v)}"
        for lbl, v, pct in zip(df_producto['tipo_producto'], df_producto['ingresos_netos'], pcts)
    ]
    fig.add_trace(go.Pie(
        labels=df_producto['tipo_producto'],
        values=df_producto['ingresos_netos'],
        marker=dict(
            colors=[colores.get(t, '#95a5a6') for t in df_producto['tipo_producto']],
            line=dict(color='white', width=2)
        ),
        text=labels_txt,
        texttemplate='%{text}',
        textfont=dict(size=10, family=FONT, weight='bold', color='white'),
        outsidetextfont=dict(size=9, family=FONT, weight='bold', color='#333'),
        insidetextorientation='horizontal',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>Ingresos: %{text}<extra></extra>',
        hole=0.44,
    ))
    fig.update_layout(
        height=260, margin=dict(t=15, b=25, l=30, r=30),
        showlegend=False,
    )
    return fig


def build_fig_heatmap(df_heatmap):
    """Heatmap: entradas por hora × día de semana. Horas en eje superior."""
    dias_order = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_num_map = {2: 'Lunes', 3: 'Martes', 4: 'Miércoles', 5: 'Jueves',
                   6: 'Viernes', 7: 'Sábado', 1: 'Domingo'}

    df = df_heatmap.copy()
    df['dia_label'] = df['dia_num'].map(dia_num_map)
    df['hora_str'] = df['hora_tour'].astype(str).str.slice(7, 12)

    horas = sorted(df['hora_str'].unique())
    matrix = []
    text_matrix = []
    for dia in dias_order:
        row = []
        text_row = []
        for hora in horas:
            mask = (df['dia_label'] == dia) & (df['hora_str'] == hora)
            val = int(df.loc[mask, 'entradas'].sum()) if mask.any() else 0
            row.append(val)
            text_row.append(str(val) if val > 0 else '')
        matrix.append(row)
        text_matrix.append(text_row)

    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=matrix,
        x=horas,
        y=dias_order,
        text=text_matrix,
        texttemplate='%{text}',
        textfont=dict(size=9, family=FONT, weight='bold'),
        colorscale=[[0, '#f0f4f8'], [0.3, '#a8d0e6'], [0.6, '#3498db'], [1, '#0d2137']],
        hovertemplate='<b>%{y} %{x}</b><br>Entradas: %{z}<extra></extra>',
        showscale=False,
    ))
    fig.update_layout(
        height=340, margin=dict(t=50, b=10, l=80, r=10),
        xaxis=dict(
            tickfont=dict(size=9, family=FONT),
            side='top',
        ),
        yaxis=dict(tickfont=dict(size=10, family=FONT), autorange='reversed'),
        plot_bgcolor='white',
    )
    return fig


def build_fig_top_horarios(df_horario):
    """Barras horizontales: top horarios por entradas."""
    df = df_horario.copy()
    df['hora_str'] = df['hora_tour'].astype(str).str.slice(7, 12)
    df = df.sort_values('entradas', ascending=True).tail(10)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['entradas'], y=df['hora_str'], orientation='h',
        marker_color=PRIMARY,
        text=[f"{fmt(v)} entradas · {fmt_eur(i)}" for v, i in zip(df['entradas'], df['ingresos'])],
        textposition='outside',
        textfont=dict(color='#333', size=9, family=FONT, weight='bold'),
        hovertemplate='<b>%{y}</b><br>Entradas: %{x}<br>Pedidos: %{customdata[0]}<extra></extra>',
        customdata=df[['pedidos']].values,
    ))
    max_x = df['entradas'].max() * 1.4 if len(df) > 0 else 100
    fig.update_layout(
        height=340, margin=dict(t=10, b=20, l=60, r=120),
        xaxis=dict(showticklabels=False, range=[0, max_x]),
        yaxis=dict(tickfont=dict(size=10, family=FONT)),
        plot_bgcolor='white',
    )
    return fig


def build_fig_canal(df_canal):
    """Donut: distribución por plataforma (mobile/desktop/tablet)."""
    # Agrupar por plataforma
    df = df_canal.groupby('plataforma').agg(
        pedidos=('pedidos', 'sum'),
        entradas=('entradas', 'sum'),
        ingresos=('ingresos', 'sum'),
    ).reset_index()

    colores_map = {'mobile': PRIMARY, 'desktop': SECONDARY, 'tablet': ACCENT}
    labels_map = {'mobile': 'Mobile', 'desktop': 'Desktop', 'tablet': 'Tablet'}
    df['label'] = df['plataforma'].map(labels_map).fillna(df['plataforma'])

    fig = go.Figure()
    total_c = df['pedidos'].sum()
    pcts_c = (df['pedidos'] / total_c * 100).round(1) if total_c > 0 else [0] * len(df)
    labels_txt_c = [
        f"<b>{lbl}</b><br>{pct:.1f}%<br>{fmt(v)} pedidos"
        for lbl, v, pct in zip(df['label'], df['pedidos'], pcts_c)
    ]
    fig.add_trace(go.Pie(
        labels=df['label'],
        values=df['pedidos'],
        marker=dict(
            colors=[colores_map.get(p, '#95a5a6') for p in df['plataforma']],
            line=dict(color='white', width=2)
        ),
        text=labels_txt_c,
        texttemplate='%{text}',
        textfont=dict(size=10, family=FONT, weight='bold', color='white'),
        outsidetextfont=dict(size=9, family=FONT, weight='bold', color='#333'),
        insidetextorientation='horizontal',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>%{text}<extra></extra>',
        hole=0.44,
    ))
    fig.update_layout(
        height=260, margin=dict(t=15, b=25, l=30, r=30),
        showlegend=False,
    )
    return fig


def build_fig_metodo_pago(df_metodo):
    """Donut: método de pago (solo TARJETA y EFECTIVO)."""
    excluir = ['DEUDA', 'TRANSFERENCIA']
    df = df_metodo[~df_metodo['metodo_pago'].isin(excluir)].copy()

    colores_map = {'TARJETA': PRIMARY, 'EFECTIVO': SECONDARY}
    colores = [colores_map.get(m, '#95a5a6') for m in df['metodo_pago']]

    fig = go.Figure()
    total_m = df['pedidos'].sum()
    pcts_m = (df['pedidos'] / total_m * 100).round(1) if total_m > 0 else [0] * len(df)
    labels_txt_m = [
        f"<b>{lbl}</b><br>{pct:.1f}%<br>{fmt(v)} pedidos"
        for lbl, v, pct in zip(df['metodo_pago'], df['pedidos'], pcts_m)
    ]
    fig.add_trace(go.Pie(
        labels=df['metodo_pago'],
        values=df['pedidos'],
        marker=dict(
            colors=colores,
            line=dict(color='white', width=2)
        ),
        text=labels_txt_m,
        texttemplate='%{text}',
        textfont=dict(size=10, family=FONT, weight='bold', color='white'),
        outsidetextfont=dict(size=9, family=FONT, weight='bold', color='#333'),
        insidetextorientation='horizontal',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>%{text}<extra></extra>',
        hole=0.44,
    ))
    fig.update_layout(
        height=260, margin=dict(t=15, b=25, l=30, r=30),
        showlegend=False,
    )
    return fig


# =============================================================================
# CALLBACK
# =============================================================================

@callback(
    Output("content-museo", "children"),
    Input("content-museo", "id"),
)
def update_page(_):
    try:
        df_kpis = get_museo_kpis()
        df_diario = get_museo_diario()
        df_producto = get_museo_producto()
        df_horario = get_museo_horario()
        df_dia_semana = get_museo_dia_semana()
        df_canal = get_museo_canal()
        df_metodo = get_museo_metodo_pago()
        df_heatmap = get_museo_heatmap()
        df_partidos = get_museo_partidos_local()

        if df_kpis.empty:
            return html.Div("No hay datos disponibles. Ejecuta sync_data.py --museo primero.",
                           style={"textAlign": "center", "padding": "40px", "color": "#999"})

        kpi = df_kpis.iloc[0]

        # --- KPI Cards ---
        kpis_row = html.Div([
            create_kpi_simple(float(kpi['ingresos_netos']), "Ingresos Totales", "euros",
                              tooltip="Ingresos netos totales de pedidos completados en el museo."),
            create_kpi_simple(int(kpi['total_entradas']), "Entradas Vendidas",
                              tooltip="Número total de entradas vendidas (pedidos completados)."),
            create_kpi_simple(float(kpi['ticket_medio']), "Ticket Medio", "euros",
                              tooltip="Importe medio por pedido completado: Ingresos ÷ Pedidos completados."),
            create_kpi_simple(float(kpi['entradas_por_pedido']), "Entradas / Pedido", "decimal",
                              tooltip="Media de entradas por cada pedido completado."),
        ], className="kpis-row")

        # --- Leyenda evolución diaria (solo Ingresos + Día de partido tras
        # eliminar la serie de Entradas para que la gráfica se enfoque en
        # facturación del museo y los hitos de jornada). ---
        legend_evolucion = html.Div([
            html.Div(style={"width": "14px", "height": "3px", "backgroundColor": PRIMARY,
                            "borderRadius": "2px", "display": "inline-block", "marginRight": "5px"}),
            html.Span("Ingresos (€)", style={"marginRight": "18px", "fontSize": "11px", "fontFamily": FONT}),
            html.Div(style={"width": "14px", "height": "3px", "backgroundColor": ACCENT,
                            "borderRadius": "2px", "display": "inline-block", "marginRight": "5px",
                            "borderTop": f"2px dashed {ACCENT}"}),
            html.Span("Día de partido", style={"fontSize": "11px", "fontFamily": FONT}),
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "4px"})

        # --- Build charts ---
        fig_evolucion = build_fig_evolucion_diaria(df_diario, df_partidos)
        fig_producto = build_fig_producto(df_producto)
        fig_heatmap = build_fig_heatmap(df_heatmap)
        fig_horarios = build_fig_top_horarios(df_horario)
        fig_canal = build_fig_canal(df_canal)
        fig_metodo = build_fig_metodo_pago(df_metodo)

        graph_cfg = {'displayModeBar': False}

        return html.Div([
            kpis_row,
            html.Div([
                # Row 1: Evolución diaria
                html.Div([
                    html.Div([
                        html.H4("Evolución Diaria de Ingresos y Entradas"),
                        legend_evolucion,
                        dcc.Graph(figure=fig_evolucion, config=graph_cfg),
                    ], className="graph-card full-width"),
                ], className="graphs-row"),

                # Row 2: 3 donuts — Tipo de Tour + Canal de Venta + Método de Pago
                html.Div([
                    html.Div([
                        html.H4("Distribución por Tipo de Tour"),
                        dcc.Graph(figure=fig_producto, config=graph_cfg),
                    ], className="graph-card"),
                    html.Div([
                        html.H4("Canal de Venta"),
                        dcc.Graph(figure=fig_canal, config=graph_cfg),
                    ], className="graph-card"),
                    html.Div([
                        html.H4("Método de Pago"),
                        dcc.Graph(figure=fig_metodo, config=graph_cfg),
                    ], className="graph-card"),
                ], className="graphs-row"),

                # Row 3: Top Horarios + Heatmap
                html.Div([
                    html.Div([
                        html.H4("Top Horarios más Demandados"),
                        dcc.Graph(figure=fig_horarios, config=graph_cfg),
                    ], className="graph-card"),
                    html.Div([
                        html.H4("Mapa de Calor según Hora y Día"),
                        dcc.Graph(figure=fig_heatmap, config=graph_cfg),
                    ], className="graph-card"),
                ], className="graphs-row"),

            ], className="graphs-container"),
        ], className="page-content-container")

    except Exception as e:
        print(f"Error en museo: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"Error: {str(e)}")
