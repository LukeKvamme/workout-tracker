from dash import html
import dash

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('This is our Home page'),
    html.Div('This is our Home page content.'),
])