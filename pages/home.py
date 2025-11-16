from dash import Dash, html, dcc, Input, Output, State, callback, callback_context
import dash

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('Home Page'),
    html.Div('Okay this is the final test'),
])
