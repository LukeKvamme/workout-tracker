from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import dash
from database import init_db

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True, suppress_callback_exceptions=True)
init_db()

app.layout = html.Div([
    html.H1('My Workout Tracker', className='p-1'),
    html.Div([
        html.Div(
            dcc.Link(f"{page['name']}", href=page['relative_path'])
        ) for page in dash.page_registry.values()
    ]),
    html.Div(dash.page_container)
])

if __name__ == '__main__':
    app.run(debug=True)