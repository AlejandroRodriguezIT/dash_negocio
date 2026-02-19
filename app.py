"""
Plataforma de Inteligencia de Negocio
======================================
RC Deportivo de La Coruña
"""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update
import dash_bootstrap_components as dbc
from database import init_users_table, validate_user

# Inicializar tabla de usuarios al arrancar
try:
    init_users_table()
except Exception as e:
    print(f"Aviso: No se pudo inicializar tabla de usuarios: {e}")

# Inicializar la aplicación
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    use_pages=True,
    pages_folder="pages"
)

app.title = "Inteligencia de Negocio - RC Deportivo"
server = app.server

# =============================================================================
# MAPA DE SECCIONES → PERMISOS
# =============================================================================
# 0 = acceso global (todas las secciones)
# 1 = Estadio ABANCA-RIAZOR
# 2 = Museo RCD
# 3 = Dépor Tiendas
# 4 = Dépor Hostelería

SECCIONES = {
    "estadio":      {"permiso": 1, "label": "ESTADIO ABANCA-RIAZOR",
                     "icon": "/assets/Indice/Estadio ABANCA-RIAZOR.png",
                     "href": "/estadio/entradas", "id": "nav-estadio"},
    "museo":        {"permiso": 2, "label": "MUSEO RCD",
                     "icon": "/assets/Indice/Museo.png",
                     "href": "/museo", "id": "nav-museo"},
    "deportiendas": {"permiso": 3, "label": "DÉPOR TIENDAS",
                     "icon": "/assets/Indice/DeporTienda.png",
                     "href": "/deportiendas", "id": "nav-deportiendas"},
    "hosteleria":   {"permiso": 4, "label": "DÉPOR HOSTELERIA",
                     "icon": "/assets/Indice/Depor_Hosteleria.png",
                     "href": "/hosteleria", "id": "nav-hosteleria"},
}


# =============================================================================
# COMPONENTES
# =============================================================================

def create_login():
    """Crea la pantalla de login."""
    return html.Div(
        className="login-wrapper",
        id="login-wrapper",
        children=[
            html.Div(
                className="login-box",
                children=[
                    html.Img(src="/assets/ESCUDO-AZUL_RGB-HD.png", className="login-shield"),
                    html.H2("Iniciar Sesión", className="login-title"),
                    dcc.Input(
                        id="login-user",
                        type="text",
                        placeholder="Usuario",
                        className="login-input",
                        autoFocus=True,
                    ),
                    dcc.Input(
                        id="login-pass",
                        type="password",
                        placeholder="Contraseña",
                        className="login-input",
                        n_submit=0,
                    ),
                    html.Div(id="login-error", className="login-error"),
                    html.Button("Entrar", id="login-btn", className="login-btn", n_clicks=0),
                ]
            )
        ]
    )


def create_header():
    """Crea el encabezado principal."""
    return html.Div(
        className="main-header",
        children=[
            html.Div(
                className="header-content",
                children=[
                    html.Img(src="/assets/escudo.png", className="header-logo"),
                    html.Div([
                        html.H1("Inteligencia de Negocio", className="header-title"),
                        html.P("RC Deportivo - Sistema de gestión integral", className="header-subtitle"),
                    ])
                ]
            )
        ]
    )


# =============================================================================
# LAYOUT PRINCIPAL
# =============================================================================

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # Session store — persiste mientras la pestaña esté abierta
    dcc.Store(id='session-store', storage_type='session'),
    # Login overlay
    create_login(),
    # App principal (oculta hasta login)
    html.Div(
        className="app-container",
        id="app-container",
        style={"display": "none"},
        children=[
            # Sidebar dinámico
            html.Div(
                className="sidebar",
                id="sidebar",
                children=[
                    html.Div(
                        className="sidebar-header",
                        children=[html.H2("DEPORTIVO", className="sidebar-title")]
                    ),
                    html.Nav(className="sidebar-nav", id="sidebar-nav"),
                    html.Div(
                        className="sidebar-footer",
                        id="sidebar-footer",
                        children=[
                            html.Div(id="user-info-text", className="user-info"),
                            html.Div(id="user-role-text", className="user-role"),
                            html.Button("Cerrar sesión", id="btn-logout", className="btn-logout", n_clicks=0),
                        ]
                    ),
                ]
            ),
            html.Div(
                className="main-content",
                children=[
                    create_header(),
                    html.Div(id="page-content", children=[dash.page_container])
                ]
            )
        ]
    )
])


# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output('session-store', 'data'),
    Output('login-error', 'children'),
    Input('login-btn', 'n_clicks'),
    Input('login-pass', 'n_submit'),
    State('login-user', 'value'),
    State('login-pass', 'value'),
    State('session-store', 'data'),
    prevent_initial_call=True,
)
def do_login(n_clicks, n_submit, usuario, contrasena, current_session):
    """Valida credenciales y guarda la sesión."""
    if current_session and current_session.get('authenticated'):
        return no_update, no_update

    if not usuario or not contrasena:
        return no_update, "Introduce usuario y contraseña"

    user = validate_user(usuario, contrasena)
    if user:
        return {
            "authenticated": True,
            "usuario": user["usuario"],
            "permisos": user["permisos"],
            "nombre": user["nombre"],
            "rol": user["rol"],
        }, ""
    return no_update, "Credenciales incorrectas"


@callback(
    Output('session-store', 'data', allow_duplicate=True),
    Input('btn-logout', 'n_clicks'),
    prevent_initial_call=True,
)
def do_logout(n_clicks):
    """Cierra sesión limpiando el store."""
    if n_clicks:
        return {"authenticated": False}
    return no_update


@callback(
    Output('login-wrapper', 'style'),
    Output('app-container', 'style'),
    Output('sidebar-nav', 'children'),
    Output('user-info-text', 'children'),
    Output('user-role-text', 'children'),
    Input('session-store', 'data'),
    Input('url', 'pathname'),
)
def toggle_login(session, pathname):
    """Muestra login u app según sesión. Construye sidebar según permisos."""
    if not session or not session.get('authenticated'):
        return (
            {"display": "flex"},   # login visible
            {"display": "none"},   # app oculta
            [],
            "",
            "",
        )

    if pathname is None:
        pathname = "/"

    permisos_raw = str(session.get('permisos', '0'))
    permisos_list = [p.strip() for p in permisos_raw.split(',')]
    is_global = '0' in permisos_list

    # Construir menú con estado activo
    inicio_cls = "nav-link active" if pathname == "/" else "nav-link"
    nav_items = [
        dcc.Link("INICIO", href="/", className=inicio_cls, id="nav-inicio"),
    ]

    path_map = {
        "estadio": "/estadio",
        "museo": "/museo",
        "deportiendas": "/deportiendas",
        "hosteleria": "/hosteleria",
    }

    for key, sec in SECCIONES.items():
        if is_global or str(sec['permiso']) in permisos_list:
            is_active = pathname.startswith(path_map.get(key, "/__none__"))
            cls = "nav-link active" if is_active else "nav-link"
            nav_items.append(
                dcc.Link([
                    html.Img(src=sec['icon'], className="nav-icon"),
                    html.Span(sec['label'])
                ], href=sec['href'], className=cls, id=sec['id'])
            )

    nombre = session.get('nombre', session.get('usuario', ''))
    rol = session.get('rol', '')

    return (
        {"display": "none"},                        # login oculta
        {"display": "flex"},                         # app visible
        nav_items,
        f"Usuario: {nombre}",
        rol,
    )


# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, port=8050)
