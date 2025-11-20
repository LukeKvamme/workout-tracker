from dash import callback_context, html, dcc, callback, Input, Output
import dash

dash.register_page(__name__)

grafana_dashboard_url = "http://192.168.1.111:3000/public-dashboards/8e29c895422d4bc1a0eff1accb92aec7"

layout = html.Div(children=[
    html.H1('Workout Stats'),
    html.Iframe(
        src=grafana_dashboard_url,
        width="100%",
        height="1450",
        style={"border": "5px solid black"}
        )
    ]
)
