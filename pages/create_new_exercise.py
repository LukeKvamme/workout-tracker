from dash import Dash, callback_context, html, dcc, Input, Output, State, callback
import dash
from sqlalchemy.orm import Session
from database import Session, Exercise, Set, Workout

dash.register_page(__name__)


# Create a session
session = Session()

# Get exercises for dropdown
exercises = session.query(Exercise).all()
muscle_groups = ['Chest', 'Back', 'Legs', 'Arms', 'Shoulders']

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
        return "Please fill in all required fields"
    
    if triggered_id == 'exercise-button':
        try:
            # Create new exercise
            new_exercise = Exercise(
                name=exercise_name,
                category=exercise_musclegroup,
                equipment=exercise_equipment,
                notes=notes
            )
            
            session.add(new_exercise)
            session.commit()
            
            return f"New Exercise logged"
        
        except Exception as e:
            session.rollback()
            return f"Error: {str(e)}"
    return ""