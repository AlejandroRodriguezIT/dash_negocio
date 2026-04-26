"""
Componentes reutilizables de la plataforma
==========================================
"""

from dash import html, dcc


# Mapa t2_name (slv_partidos) -> archivo PNG en /assets/Escudos/
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
    'Racing': 'Real Racing Club.png',
    'Racing de Santander': 'Real Racing Club.png',
    'Real Racing Club': 'Real Racing Club.png',
    'Real Sociedad B': 'Real Sociedad B.png',
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


def get_escudo_path(t2_name):
    """Devuelve la ruta del escudo en /assets/Escudos/<archivo> o None."""
    archivo = ESCUDOS_MAP.get(t2_name)
    return f"/assets/Escudos/{archivo}" if archivo else None


def _escudo_slot(rival, id_partido, tiene_ficha, active_id=None):
    """Renderiza un único slot (círculo con escudo).

    - tiene_ficha=True  → slot habilitado, clickable a /ficha-partido/<id>
    - tiene_ficha=False → slot deshabilitado (gris), no clickable
    - active_id==id_partido → slot marcado como activo (azul corporativo)
    """
    escudo = get_escudo_path(rival)
    img = html.Img(src=escudo, alt=rival) if escudo else html.Span(rival)

    classes = ["escudo-slot"]
    if not tiene_ficha:
        classes.append("escudo-slot--disabled")
    else:
        classes.append("escudo-slot--enabled")
        if active_id is not None and int(id_partido or 0) == int(active_id):
            classes.append("escudo-slot--active")

    slot = html.Div(img, className=" ".join(classes), title=rival)

    if tiene_ficha and id_partido is not None:
        return dcc.Link(
            slot,
            href=f"/ficha-partido/{int(id_partido)}",
            className="escudo-slot-link",
        )
    return html.Div(slot, className="escudo-slot-link")


def build_escudos_nav(df_rivales, layout="grid", active_id=None, title="FICHA POST PARTIDO"):
    """Construye el navegador de escudos.

    Args:
        df_rivales: DataFrame con columnas t2_name, id_partido, tiene_ficha (0/1).
        layout: "grid" (2 filas × 11) para home o "ficha" (1 fila horizontal).
        active_id: id_partido del partido actual en una ficha (resalta el slot).
        title: Título superior (solo se muestra en layout="grid").
    """
    if df_rivales is None or df_rivales.empty:
        return html.Div()

    # Lista ordenada de slots
    slots = []
    for _, row in df_rivales.iterrows():
        rival = row.get('t2_name')
        id_partido = row.get('id_partido')
        tiene_ficha = bool(row.get('tiene_ficha', 0))
        slots.append(_escudo_slot(rival, id_partido, tiene_ficha, active_id=active_id))

    if layout == "ficha":
        # Una sola fila horizontal con scroll si excede
        return html.Div(slots, className="escudos-nav-ficha")

    # Layout grid: 2 filas equiespaciadas. Reparte slots en dos mitades.
    mid = (len(slots) + 1) // 2
    row1 = html.Div(slots[:mid], className="escudos-nav-row")
    row2 = html.Div(slots[mid:], className="escudos-nav-row")

    return html.Div([
        html.H3(title, className="escudos-nav-title"),
        html.Div([row1, row2], className="escudos-nav-rows"),
    ], className="escudos-nav-section")
