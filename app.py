from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import dash
from database import init_db

init_db()
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
server = app.server # gunicorn thing, crazy this is all it needs
app.title = "Workout Tracker"

dcc_link_style = {
    'margin': '30px',
    'padding': '10px 40px',
    'textDecoration': 'none',
    'color': 'black',
    'font-size': '22px',
    'border-color': "#bebcbc",
    'borderRadius': '5px',
    'hover': {'backgroundColor': "#1F71B4"}
}

app.layout = html.Div([
    html.Div([
        dcc.Location(id='url'), # tracks current url/path, but rn not used (could be used with callback)
        html.Div([
                    html.Div(dcc.Link(
                        "Home",
                        href="/",
                        id="link-home",
                        style=dcc_link_style
                    )),
                    html.Div(dcc.Link(
                        "View Analytics",
                        href="/analytics",
                        style=dcc_link_style
                    )),
                    html.Div(dcc.Link(
                        "Create New Exercise",
                        href="/create-new-exercise",
                        id="create-exercise-link",
                        style=dcc_link_style
                    )),
                    html.Div(dcc.Link(
                        "Log Workout Set",
                        href="/log-set",
                        id="log-set-link",
                        style=dcc_link_style
                    ))], style={
                        "backgroundColor": "#c7c9ca",
                        "padding": "10px",
                        "borderRadius": "5px",
                        "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.1)"
                    }
        ),
        html.Div(
            children=[dash.page_container],
            style={
                "margin-top": "20px", 
                "padding": "20px",
                "border": "1px solid #ddd",
                "border-radius": "5px",
                "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)",
                "backgroundColor": "#c7c9ca"
                }
        )
    ], style = {
        "backgroundColor": "#ffffff",
        "font-family": "Arial, sans-serif",
        "max-width": "900px",
        "max-height": "100%",
        "margin": "auto",
        "padding": "20px"
    }
    )
])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)