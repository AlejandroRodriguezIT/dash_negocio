"""
Página Dépor Tiendas
=====================
Análisis de ventas retail: tiendas físicas + online.
"""

import dash
from dash import html, dcc, callback, Output, Input
import plotly.graph_objects as go
import pandas as pd
from database import (
    get_pre_deportiendas_kpis, get_pre_deportiendas_matchday,
    get_pre_deportiendas_por_tienda, get_pre_deportiendas_top_productos,
    get_pre_deportiendas_producto_tienda, get_pre_deportiendas_canal,
)

dash.register_page(__name__, path="/deportiendas", name="Dépor Tiendas")


# =============================================================================
# HELPERS
# =============================================================================

ESCUDOS_MAP = {
    'Albacete': 'Albacete BP.png', 'Albacete BP': 'Albacete BP.png',
    'Atlético de Madrid': 'Atletico de Madrid.png', 'Atletico de Madrid': 'Atletico de Madrid.png',
    'Burgos': 'Burgos CF.png', 'Burgos CF': 'Burgos CF.png',
    'Castellón': 'CD Castellón.png', 'CD Castellón': 'CD Castellón.png',
    'Leganés': 'CD Leganés.png', 'CD Leganés': 'CD Leganés.png',
    'Mirandés': 'CD Mirandés.png', 'CD Mirandés': 'CD Mirandés.png',
    'Ceuta': 'Ceuta.png', 'AD Ceuta': 'Ceuta.png', 'AD Ceuta FC': 'Ceuta.png',
    'Cultural Leonesa': 'Cultural.png', 'Cultural': 'Cultural.png',
    'Cádiz': 'Cádiz CF.png', 'Cádiz CF': 'Cádiz CF.png',
    'Córdoba': 'Córdoba CF.png', 'Córdoba CF': 'Córdoba CF.png',
    'Granada': 'Granada CF.png', 'Granada CF': 'Granada CF.png',
    'Le Havre': 'Le Havre.png',
    'Mallorca': 'Mallorca.png', 'RCD Mallorca': 'Mallorca.png',
    'Málaga': 'Málaga CF.png', 'Málaga CF': 'Málaga CF.png',
    'Racing': 'Real Racing Club.png', 'Real Racing Club': 'Real Racing Club.png',
    'Real Sociedad B': 'Real Sociedad B.png', 'Real Sociedad II': 'Real Sociedad B.png',
    'Sporting': 'Real Sporting.png', 'Real Sporting': 'Real Sporting.png',
    'Valladolid': 'Real Valladolid CF.png', 'Real Valladolid': 'Real Valladolid CF.png',
    'Real Valladolid CF': 'Real Valladolid CF.png',
    'Zaragoza': 'Real Zaragoza.png', 'Real Zaragoza': 'Real Zaragoza.png',
    'Eibar': 'SD Eibar.png', 'SD Eibar': 'SD Eibar.png',
    'Huesca': 'SD Huesca.png', 'SD Huesca': 'SD Huesca.png',
    'Almería': 'UD Almería.png', 'UD Almería': 'UD Almería.png',
}


def get_escudo_path(team_name):
    f = ESCUDOS_MAP.get(team_name)
    return f"/assets/Escudos/{f}" if f else None


def fmt(val):
    return f"{val:,.0f}".replace(",", ".")


def get_result_color(result_str):
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
    images, shapes = [], []
    for i, (rival, result) in enumerate(zip(rivales, results)):
        color = get_result_color(result)
        shapes.append(dict(
            type="circle", xref="x", yref="paper",
            x0=i - 0.30, x1=i + 0.30, y0=y_pos - 0.06, y1=y_pos + 0.06,
            line=dict(color=color, width=2.5),
            fillcolor="rgba(0,0,0,0)", layer="below"
        ))
        escudo_path = get_escudo_path(rival)
        if escudo_path:
            images.append(dict(
                source=escudo_path, xref="x", yref="paper",
                x=i, y=y_pos, sizex=sizex, sizey=sizey,
                xanchor="center", yanchor="middle"
            ))
    return images, shapes


def truncate(text, max_len=40):
    return text if len(text) <= max_len else text[:max_len - 1] + '…'


def abbreviate_product(name):
    """Abrevia nombre de producto quitando referencias al club y simplificando."""
    import re
    s = str(name)
    # Quitar referencias al club
    for pattern in ['RC DEPORTIVO DE LA CORUÑA', 'DEPORTIVO DE LA CORUÑA',
                    'Deportivo de la Coruña', 'DEPORTIVO', 'Deportivo']:
        s = s.replace(pattern, '').strip()
    # Limpiar dobles espacios y guiones sueltos
    s = re.sub(r'\s{2,}', ' ', s)
    s = re.sub(r'^\s*-\s*', '', s)
    s = re.sub(r'\s*-\s*$', '', s)
    # Abreviar colores/variantes largos de sponsors
    s = s.replace('White Antique-Azure-Gold-', '')
    # Limpiar de nuevo
    s = re.sub(r'\s{2,}', ' ', s).strip()
    s = re.sub(r'^\s*-\s*', '', s).strip()
    return s


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
        html.Div("DÉPOR TIENDAS", className="section-title"),
    ], className="section-header"),
    dcc.Loading(
        id="loading-deportiendas",
        type="default",
        fullscreen=False,
        children=html.Div(id="content-deportiendas", children=loading_component()),
        custom_spinner=loading_component(),
    )
])


# =============================================================================
# CHART BUILDERS
# =============================================================================

def build_fig_por_tienda(df_tienda, df_prod_tienda):
    """Barras horizontales: facturación por tienda. Hover = top 10 productos."""
    df = df_tienda.sort_values('total_sales', ascending=True)

    hover_texts = []
    for _, row in df.iterrows():
        base = f"<b>{row['tienda']}</b><br>Facturación: {fmt(row['total_sales'])}€"
        sub = df_prod_tienda[df_prod_tienda['tienda'] == row['tienda']]
        top = sub.nlargest(10, 'uds_vendidas')
        if not top.empty:
            base += "<br><br><b>Top 10 productos:</b>"
            for i, (_, p) in enumerate(top.iterrows()):
                base += f"<br>  {i+1}. {abbreviate_product(p['product_title'])} ({fmt(p['uds_vendidas'])} uds)"
        hover_texts.append(base)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['total_sales'], y=df['tienda'], orientation='h',
        marker_color='#18395c',
        text=[fmt(v) + '€' for v in df['total_sales']],
        textposition='outside',
        textfont=dict(color='#333', size=11, family='Montserrat', weight='bold'),
        hovertext=hover_texts, hoverinfo='text',
    ))
    max_x = df['total_sales'].max() * 1.25 if len(df) > 0 else 100
    fig.update_layout(
        height=280, margin=dict(t=10, b=20, l=200, r=60),
        xaxis=dict(showticklabels=False, range=[0, max_x]),
        yaxis=dict(tickfont=dict(size=11, family='Montserrat')),
    )
    return fig


def build_fig_top_productos(df_top, df_prod_tienda):
    """Top 10 productos por unidades vendidas. Hover = tiendas por uds."""
    df = df_top.sort_values('uds_vendidas', ascending=True)

    labels = [abbreviate_product(t) for t in df['product_title']]
    hover_texts = []
    for _, row in df.iterrows():
        base = f"<b>{row['product_title']}</b>"
        base += f"<br>Uds: {fmt(row['uds_vendidas'])} · Facturación: {fmt(row['total_sales'])}€"
        sub = df_prod_tienda[df_prod_tienda['product_title'] == row['product_title']]
        top = sub.nlargest(4, 'uds_vendidas')
        if not top.empty:
            base += "<br><br><b>Por tienda:</b>"
            for i, (_, p) in enumerate(top.iterrows()):
                base += f"<br>  {i+1}. {p['tienda']} ({fmt(p['uds_vendidas'])} uds)"
        hover_texts.append(base)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['uds_vendidas'],
        y=labels,
        orientation='h', marker_color='#18395c',
        text=[fmt(v) + ' uds' for v in df['uds_vendidas']],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertext=hover_texts, hoverinfo='text',
    ))
    max_x = df['uds_vendidas'].max() * 1.30 if len(df) > 0 else 100
    fig.update_layout(
        height=380, margin=dict(t=10, b=20, l=280, r=60),
        xaxis=dict(showticklabels=False, range=[0, max_x]),
        yaxis=dict(tickfont=dict(size=9, family='Montserrat')),
    )
    return fig


def build_fig_canal(df_canal):
    """Donut: desglose punto de venta."""
    colores = {'Tienda Física': '#18395c', 'Tienda Online': '#3498db'}
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=df_canal['canal'],
        values=df_canal['total_sales'],
        marker=dict(colors=[colores.get(c, '#95a5a6') for c in df_canal['canal']],
                    line=dict(color='white', width=2)),
        textinfo='label+percent',
        textfont=dict(size=12, family='Montserrat', weight='bold', color='white'),
        outsidetextfont=dict(size=11, family='Montserrat', weight='bold', color='#333'),
        insidetextorientation='horizontal',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>Facturación: %{value:,.0f}€<br>%{percent}<extra></extra>',
        hole=0.40,
    ))
    fig.update_layout(
        height=280, margin=dict(t=10, b=20, l=20, r=20),
        showlegend=False,
    )
    return fig


def build_fig_dia_semana(df_matchday):
    """Barras agrupadas 24/25 vs 25/26: promedio ventas matchday Riazor por día."""
    df = df_matchday.copy()
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['dow'] = df['fecha'].dt.dayofweek
    # Agrupar L/M/X/J (0-3) como Intersemanales
    df['categoria'] = df['dow'].apply(lambda d: 'Intersemanales' if d <= 3 else
                                       {4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}[d])
    cat_order = ['Intersemanales', 'Viernes', 'Sábado', 'Domingo']

    grouped = df.groupby(['temporada', 'categoria']).agg(
        total=('ventas_riazor', 'sum'),
        n_partidos=('ventas_riazor', 'count'),
    ).reset_index()
    grouped['promedio'] = (grouped['total'] / grouped['n_partidos']).round(0)

    actual = grouped[grouped['temporada'] == 'actual']
    anterior = grouped[grouped['temporada'] == 'anterior']

    present_cats = [c for c in cat_order if c in actual['categoria'].values or c in anterior['categoria'].values]

    def get_vals(sub, cats):
        m = sub.set_index('categoria')
        return ([m.loc[c, 'promedio'] if c in m.index else 0 for c in cats],
                [int(m.loc[c, 'n_partidos']) if c in m.index else 0 for c in cats],
                [m.loc[c, 'total'] if c in m.index else 0 for c in cats])

    p_ant, n_ant, t_ant = get_vals(anterior, present_cats)
    p_act, n_act, t_act = get_vals(actual, present_cats)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='24/25', x=present_cats, y=p_ant,
        marker_color='#3498db',
        text=[fmt(v) + '€' if v > 0 else '' for v in p_ant],
        textposition='outside',
        textfont=dict(color='#333', size=9, family='Montserrat', weight='bold'),
        hovertext=[f"<b>{c} (24/25)</b><br>Promedio: {fmt(p)}€<br>Partidos: {n}<br>Total: {fmt(t)}€"
                   for c, p, n, t in zip(present_cats, p_ant, n_ant, t_ant)],
        hoverinfo='text',
    ))
    fig.add_trace(go.Bar(
        name='25/26', x=present_cats, y=p_act,
        marker_color='#18395c',
        text=[fmt(v) + '€' if v > 0 else '' for v in p_act],
        textposition='outside',
        textfont=dict(color='#333', size=9, family='Montserrat', weight='bold'),
        hovertext=[f"<b>{c} (25/26)</b><br>Promedio: {fmt(p)}€<br>Partidos: {n}<br>Total: {fmt(t)}€"
                   for c, p, n, t in zip(present_cats, p_act, n_act, t_act)],
        hoverinfo='text',
    ))

    max_y = max(max(p_ant + [0]), max(p_act + [0])) * 1.25
    fig.update_layout(
        barmode='group', height=350, margin=dict(t=10, b=30, l=20, r=20),
        xaxis=dict(tickfont=dict(size=11, family='Montserrat')),
        yaxis=dict(showticklabels=False, range=[0, max_y]),
        showlegend=False,
    )
    return fig


def build_fig_franja_horaria(df_matchday):
    """Barras agrupadas 24/25 vs 25/26: promedio ventas matchday Riazor por franja horaria."""
    df = df_matchday.copy()
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['hora'] = df['fecha'].apply(lambda x: x.strftime('%H:%M'))

    grouped = df.groupby(['temporada', 'hora']).agg(
        total=('ventas_riazor', 'sum'),
        n_partidos=('ventas_riazor', 'count'),
    ).reset_index()
    grouped['promedio'] = (grouped['total'] / grouped['n_partidos']).round(0)

    actual = grouped[grouped['temporada'] == 'actual'].sort_values('hora')
    anterior = grouped[grouped['temporada'] == 'anterior'].sort_values('hora')

    all_hours = sorted(set(actual['hora'].tolist() + anterior['hora'].tolist()))

    def get_vals(sub, hours):
        m = sub.set_index('hora')
        return ([m.loc[h, 'promedio'] if h in m.index else 0 for h in hours],
                [int(m.loc[h, 'n_partidos']) if h in m.index else 0 for h in hours],
                [m.loc[h, 'total'] if h in m.index else 0 for h in hours])

    p_ant, n_ant, t_ant = get_vals(anterior, all_hours)
    p_act, n_act, t_act = get_vals(actual, all_hours)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='24/25', x=all_hours, y=p_ant,
        marker_color='#3498db',
        text=[fmt(v) + '€' if v > 0 else '' for v in p_ant],
        textposition='outside',
        textfont=dict(color='#333', size=9, family='Montserrat', weight='bold'),
        hovertext=[f"<b>{h} (24/25)</b><br>Promedio: {fmt(p)}€<br>Partidos: {n}<br>Total: {fmt(t)}€"
                   for h, p, n, t in zip(all_hours, p_ant, n_ant, t_ant)],
        hoverinfo='text',
    ))
    fig.add_trace(go.Bar(
        name='25/26', x=all_hours, y=p_act,
        marker_color='#18395c',
        text=[fmt(v) + '€' if v > 0 else '' for v in p_act],
        textposition='outside',
        textfont=dict(color='#333', size=9, family='Montserrat', weight='bold'),
        hovertext=[f"<b>{h} (25/26)</b><br>Promedio: {fmt(p)}€<br>Partidos: {n}<br>Total: {fmt(t)}€"
                   for h, p, n, t in zip(all_hours, p_act, n_act, t_act)],
        hoverinfo='text',
    ))

    max_y = max(max(p_ant + [0]), max(p_act + [0])) * 1.25
    fig.update_layout(
        barmode='group', height=350, margin=dict(t=10, b=30, l=20, r=20),
        xaxis=dict(tickfont=dict(size=11, family='Montserrat'), title='Hora de Inicio'),
        yaxis=dict(showticklabels=False, range=[0, max_y]),
        showlegend=False,
    )
    return fig


def build_fig_matchday(df_matchday_actual):
    """Barras con escudos: ventas Riazor por día de partido."""
    df = df_matchday_actual.sort_values('fecha')
    rivales = df['rival'].tolist()
    results = df['resultado'].tolist()
    ventas = df['ventas_riazor'].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(range(len(rivales))), y=ventas,
        marker_color='#f39c12',
        text=[fmt(v) + '€' if v > 0 else '—' for v in ventas],
        textposition='outside',
        textfont=dict(color='#333', size=10, family='Montserrat', weight='bold'),
        hovertemplate='<b>%{customdata}</b><br>Ventas Riazor: %{y:,.0f}€<extra></extra>',
        customdata=rivales,
    ))

    escudos_images, result_shapes = create_escudos_with_result(rivales, results)
    max_y = max(ventas) * 1.15 if ventas and max(ventas) > 0 else 100

    fig.update_layout(
        margin=dict(b=50, t=5, l=20, r=20), height=350,
        images=escudos_images, shapes=result_shapes,
        xaxis=dict(
            tickmode='array', tickvals=list(range(len(rivales))),
            ticktext=['' for _ in rivales], showticklabels=False,
            range=[-0.5, len(rivales) - 0.5] if rivales else [0, 1]
        ),
        yaxis=dict(showticklabels=False, range=[0, max_y]),
    )
    return fig


# =============================================================================
# KPI CARDS
# =============================================================================

def create_kpi_simple(valor, label, formato="numero"):
    """KPI card sin comparativa (solo 25/26)."""
    if formato == "euros":
        texto = f"{fmt(valor)}€"
    else:
        texto = fmt(valor)
    return html.Div([
        html.Div(label, className="kpi-label-top",
                 style={"whiteSpace": "nowrap"}),
        html.Div(texto, className="kpi-value kpi-value-positive",
                 style={"textAlign": "center"}),
    ], className="kpi-card")


def create_kpi_comparativa(valor_actual, valor_anterior, label, small_title=False):
    """KPI card con comparativa matchday Riazor."""
    texto_actual = f"{fmt(valor_actual)}€"
    texto_anterior = f"{fmt(valor_anterior)}€"
    if valor_anterior > 0:
        pct = ((valor_actual - valor_anterior) / valor_anterior) * 100
        pct_text = f"+{pct:.1f}%" if pct >= 0 else f"{pct:.1f}%"
        color_class = "kpi-value-positive" if pct >= 0 else "kpi-value-negative"
    else:
        pct_text = "N/A"
        color_class = "kpi-value-positive"
    title_style = {"whiteSpace": "nowrap"}
    if small_title:
        title_style["fontSize"] = "11px"
    return html.Div([
        html.Div(label, className="kpi-label-top", style=title_style),
        html.Div([
            html.Span(texto_actual, className=f"kpi-value {color_class}"),
            html.Span(f" ({pct_text})", className=f"kpi-pct-diff {color_class}")
        ], style={"display": "flex", "alignItems": "baseline", "justifyContent": "center", "gap": "5px"}),
        html.Div(f"Temp. 24/25: {texto_anterior}", className="kpi-previous"),
    ], className="kpi-card")


# =============================================================================
# CALLBACK
# =============================================================================

@callback(
    Output("content-deportiendas", "children"),
    Input("content-deportiendas", "id"),
)
def update_page(_):
    try:
        df_kpis = get_pre_deportiendas_kpis()
        df_matchday = get_pre_deportiendas_matchday()
        df_tienda = get_pre_deportiendas_por_tienda()
        df_top_prod = get_pre_deportiendas_top_productos()
        df_prod_tienda = get_pre_deportiendas_producto_tienda()
        df_canal = get_pre_deportiendas_canal()

        if df_kpis.empty:
            return html.Div("No hay datos disponibles. Ejecuta compute_aggregations.py primero.")

        # KPIs
        kpi = df_kpis.iloc[0]
        rec_total = kpi['recaudacion_total']
        ben_total = kpi['beneficio_total']
        num_ventas = kpi['num_ventas']
        ticket = kpi['ticket_promedio']

        # Matchday comparison
        df_match_actual = df_matchday[df_matchday['temporada'] == 'actual']
        df_match_anterior = df_matchday[df_matchday['temporada'] == 'anterior']
        rec_matchday_actual = df_match_actual['ventas_riazor'].sum()
        rec_matchday_anterior = df_match_anterior['ventas_riazor'].sum()

        kpis_row = html.Div([
            create_kpi_comparativa(rec_matchday_actual, rec_matchday_anterior,
                                   "Ventas Matchday Riazor 25/26", small_title=True),
            create_kpi_simple(rec_total, "Recaudación Total 25/26", "euros"),
            create_kpi_simple(ben_total, "Beneficio Total 25/26", "euros"),
            create_kpi_simple(num_ventas, "Nº Ventas Total 25/26"),
            create_kpi_simple(ticket, "Ticket Promedio 25/26", "euros"),
        ], className="kpis-row")

        # Charts
        fig_matchday = build_fig_matchday(df_match_actual)
        fig_tienda = build_fig_por_tienda(df_tienda, df_prod_tienda)
        fig_canal = build_fig_canal(df_canal)
        fig_top_prod = build_fig_top_productos(df_top_prod, df_prod_tienda)
        fig_dia = build_fig_dia_semana(df_matchday)
        fig_franja = build_fig_franja_horaria(df_matchday)

        # Leyenda HTML reutilizable para gráficas comparativas
        legend_row = html.Div([
            html.Div(style={"width": "14px", "height": "14px", "backgroundColor": "#3498db",
                            "borderRadius": "3px", "display": "inline-block", "marginRight": "5px"}),
            html.Span("24/25", style={"marginRight": "18px", "fontSize": "12px", "fontFamily": "Montserrat"}),
            html.Div(style={"width": "14px", "height": "14px", "backgroundColor": "#18395c",
                            "borderRadius": "3px", "display": "inline-block", "marginRight": "5px"}),
            html.Span("25/26", style={"fontSize": "12px", "fontFamily": "Montserrat"}),
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "4px"})

        return html.Div([
            kpis_row,
            html.Div([
                # Row 1: Matchday Riazor
                html.Div([
                    html.Div([
                        html.H4("Ventas Matchday Riazor 25/26"),
                        dcc.Graph(figure=fig_matchday, config={'displayModeBar': False}),
                    ], className="graph-card full-width"),
                ], className="graphs-row"),
                # Row 2: Día de la semana
                html.Div([
                    html.Div([
                        html.H4("Ventas Matchday Riazor por Día de la Semana"),
                        legend_row,
                        dcc.Graph(figure=fig_dia, config={'displayModeBar': False}),
                    ], className="graph-card full-width"),
                ], className="graphs-row"),
                # Row 3: Franja horaria
                html.Div([
                    html.Div([
                        html.H4("Ventas Matchday Riazor por Franja Horaria"),
                        legend_row,
                        dcc.Graph(figure=fig_franja, config={'displayModeBar': False}),
                    ], className="graph-card full-width"),
                ], className="graphs-row"),
                # Row 4: Top productos
                html.Div([
                    html.Div([
                        html.H4("Top 10 Productos más Vendidos 25/26"),
                        dcc.Graph(figure=fig_top_prod, config={'displayModeBar': False}),
                    ], className="graph-card full-width"),
                ], className="graphs-row"),
                # Row 5: Facturación por tienda + Desglose
                html.Div([
                    html.Div([
                        html.H4("Facturación por Tienda 25/26"),
                        dcc.Graph(figure=fig_tienda, config={'displayModeBar': False}),
                    ], className="graph-card"),
                    html.Div([
                        html.H4("Desglose Punto de Venta 25/26"),
                        dcc.Graph(figure=fig_canal, config={'displayModeBar': False}),
                    ], className="graph-card"),
                ], className="graphs-row"),
            ], className="graphs-container"),
        ], className="page-content-container")

    except Exception as e:
        print(f"Error en deportiendas: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"Error: {str(e)}")
