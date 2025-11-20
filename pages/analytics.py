from dash import callback_context, html, dcc, callback, Input, Output
from flask import request
import dash

dash.register_page(__name__)

local_grafana_dashboard_url = "http://192.168.1.111:3000/public-dashboards/8e29c895422d4bc1a0eff1accb92aec7"
tailscale_grafana_dashboard_url = "http://100.100.143.61:3000/public-dashboards/8e29c895422d4bc1a0eff1accb92aec7"

layout = html.Div(children=[
    html.H1('Workout Stats'),
    html.Iframe(
        id="grafana-output",
        src=tailscale_grafana_dashboard_url, # tailscale default value bcz >90% access from gym
        width="100%",
        height="1450",
        style={"border": "5px solid black"}
        ),
    html.Div(id="dummy-hidden-div", style={"display": "none"})
    ]
)

@callback(
    Output('grafana-output', 'src'),
    Input('dummy-hidden-div', 'children')
)
def get_connection_url(children):
    if request.remote_addr.startswith("100."):
        return tailscale_grafana_dashboard_url
    else:
        return local_grafana_dashboard_url
