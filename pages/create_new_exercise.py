from dash import Dash, callback_context, html, dcc, Input, Output, State, callback
import dash
from database import execute_query, new_exercise

dash.register_page(__name__)

# get muyscle groups for dropdown
muscle_group_tuple = execute_query("""SELECT DISTINCT muscle_group FROM `exercises`;""")
muscle_groups = []
for muscle in muscle_group_tuple:
    muscle_groups.append(muscle["muscle_group"])


layout = html.Div([
    html.H2("Create a new Exercise"),
    
    
    dcc.Input(id='name-input', type='text', placeholder='Exercise Name'),
    dcc.Dropdown(
        id='category-group-dropdown',
        options=muscle_groups,
        placeholder="Select Muscle Group"
    ),
    dcc.Input(id='equipment-type-input', type='text', placeholder='Equipment Type'),
    
    dcc.Textarea(
        id='notes-textarea',
        placeholder='Notes (optional)',
        style={'width': '100%', 'height': 100}
    ),
    
    html.Button('Add New Exercise', id='exercise-button', n_clicks=0),
    html.Div(id='exercise-output-message')
])

@callback(
    Output('exercise-output-message', 'children'),
    Input('exercise-button', 'n_clicks'),
    State('name-input', 'value'),
    State('category-group-dropdown', 'value'),
    State('equipment-type-input', 'value'),
    State('notes-textarea', 'value'),
    prevent_initial_call=True
)
def log_new_exercise(n_clicks, exercise_name, exercise_musclegroup, exercise_equipment, notes):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if not all([exercise_name, exercise_musclegroup, exercise_equipment]):
        return "Please fill in all required fields."
    
    if triggered_id == 'exercise-button':
        status = new_exercise(name=exercise_name, description=notes, muscle_group=exercise_musclegroup, equipment=exercise_equipment)
    return