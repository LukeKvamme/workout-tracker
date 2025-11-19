from dash import Dash, callback_context, html, dcc, Input, Output, State, callback
import dash
from database import execute_query, new_exercise

dash.register_page(__name__, path='/create-new-exercise')

# get muscle groups for dropdown
muscle_group_tuple = execute_query("""SELECT DISTINCT muscle_group FROM `exercises`;""")
muscle_groups = []
for muscle in muscle_group_tuple:
    muscle_groups.append(muscle["muscle_group"])

# get equipment for dropdown
equipment_tuple = execute_query("""SELECT DISTINCT equipment FROM `exercises`;""")
equipment_list = []
for equipment in equipment_tuple:
    equipment_list.append(equipment["equipment"])

muscle_groups.sort()
equipment_list.sort()

layout = html.Div([
    html.H1("Create a New Exercise"),
    
    dcc.Input(
        id='name-input', 
        type='text', 
        placeholder='Exercise Name',
        style={
            'width': '97%', 
            'marginBottom': '15px',
            'padding': '8px',
            'fontSize': '16px'
            }
        ),
    dcc.Dropdown(
        id='category-group-dropdown',
        options=muscle_groups,
        placeholder="Select Muscle Group",
        style={
            'width': '100%', 
            'marginBottom': '5px',
            'padding': '10px',
            'fontSize': '16px'
            }
    ),
    dcc.Dropdown(
        id='equipment-type-dropdown',
        options=equipment_list,
        placeholder="Select Equipment Type",
        style={
            'width': '100%', 
            'marginBottom': '5px',
            'padding': '8px',
            'fontSize': '16px'
            }
    ),
    
    dcc.Textarea(
        id='notes-textarea',
        placeholder='Notes (optional)',
        style={
            'width': '97%', 
            'height': 70,
            'marginBottom': '10px',
            'padding': '8px',
            'fontSize': '18px'
            }
    ),
    
    html.Button('Add New Exercise', 
                id='exercise-button',
                style={
                    'marginTop': '10px',
                    'padding': '15px 100px',
                    'fontSize': '16px',
                    'backgroundColor': "#2510A0",
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '10px',
                    'cursor': 'pointer'
                },
                n_clicks=0),
    html.Div(id='exercise-output-message')
])

@callback(
    Output('exercise-output-message', 'children'),
    Input('exercise-button', 'n_clicks'),
    State('name-input', 'value'),
    State('category-group-dropdown', 'value'),
    State('equipment-type-dropdown', 'value'),
    State('notes-textarea', 'value'),
    prevent_initial_call=True
)
def log_new_exercise(n_clicks, exercise_name, exercise_musclegroup, exercise_equipment, notes):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if not all([exercise_name, exercise_musclegroup, exercise_equipment]):
        return "Please fill in all required fields."
    
    if triggered_id == 'exercise-button':
        new_exercise(name=exercise_name, description=notes, muscle_group=exercise_musclegroup, equipment=exercise_equipment)
    return f"New exercise added: {exercise_name}.\nMuscle Group: {exercise_musclegroup}.\nEquipment: {exercise_equipment}."