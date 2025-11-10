from dash import html
import dash

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('IDK What else to put here'),
    html.Div('But I am changing things so i can watch the ci/cd pipeline work and update production with this lol.'),
])