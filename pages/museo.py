"""
Página Museo RCD
=================
"""

import dash
from dash import html

dash.register_page(__name__, path="/museo", name="Museo RCD")

layout = html.Div(
    className="page-content-container",
    style={"display": "flex", "alignItems": "center", "justifyContent": "center", "minHeight": "60vh"},
    children=[
        html.H2("Pendiente de desarrollo",
                 style={"color": "#999", "fontFamily": "Montserrat", "fontWeight": "500"})
    ]
)
