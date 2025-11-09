from dash import callback_context, html, dcc, callback, Input, Output
import dash

dash.register_page(__name__)

muscle_groups = ['Chest', 'Back', 'Legs', 'Arms', 'Shoulders']

layout = html.Div([
    html.H1('This is the Analytics page'),
    html.Div([
        "Select a muscle group:",
        dcc.RadioItems(
            options=muscle_groups,
            value='musclegroup',
            id='analytics-input'
        )
    ]),
    html.Br(),
    html.Div(id='analytics-output'),
])


@callback(
    Output('analytics-output', 'children'),
    Input('analytics-input', 'value')
)
def update_city_selected(input_value):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'analytics-input':
        if input_value in muscle_groups:
            return f'You selected: {input_value}'
        else:
            return "Please select a muscle group"