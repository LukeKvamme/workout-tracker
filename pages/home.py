from dash import html
import dash

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('TEST TEST TEST ETST TEST'),
    html.Div('Okay this is the final test'),
])