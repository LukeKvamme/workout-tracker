from dash import Dash, html, dcc, Input, Output, State, callback, callback_context
import dash
from database import execute_query

dash.register_page(__name__)


# get exercises for dropdown
exercise_options = execute_query("""SELECT * FROM `exercises`""")
# exercise_options = [{'label': ex.name, 'value': ex.id} for ex in exercises]

layout = html.Div([
    html.H2("Log Workout Set"),
    
    dcc.Dropdown(
        id='exercise-dropdown',
        options=exercise_options,
        placeholder="Select Exercise"
    ),
    
    dcc.Input(id='weight-input', type='number', placeholder='Weight (lbs)'),
    dcc.Input(id='reps-input', type='number', placeholder='Reps'),
    dcc.Input(id='set-number-input', type='number', placeholder='Set Number'),
    
    dcc.Textarea(
        id='notes-textarea',
        placeholder='Notes (optional)',
        style={'width': '100%', 'height': 100}
    ),
    
    html.Button('Log Set', id='submit-button', n_clicks=0),
    html.Div(id='set-output-message')
])

@callback(
    Output('set-output-message', 'children'),
    Input('submit-button', 'n_clicks'),
    State('exercise-dropdown', 'value'),
    State('weight-input', 'value'),
    State('reps-input', 'value'),
    State('set-number-input', 'value'),
    State('notes-textarea', 'value'),
    prevent_initial_call=True
)
def log_workout_set(n_clicks, exercise_id, weight, reps, set_number, notes):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if not all([exercise_id, weight, reps]):
        return "Please fill in all required fields"
    
    if triggered_id == 'submit-button':
        try:
            # Get or create today's workout
            from datetime import datetime
            today = datetime.now().date()
            workout = session.query(Workout).filter(
                Workout.date >= datetime.combine(today, datetime.min.time())
            ).first()
            
            if not workout:
                workout = Workout(date=datetime.now(), name="Today's Workout")
                session.add(workout)
                session.flush()  # Get the workout.id
            
            # Create new set
            new_set = Set(
                workout_id=workout.id,
                exercise_id=exercise_id,
                weight=weight,
                reps=reps,
                set_number=set_number,
                notes=notes
            )
            
            session.add(new_set)
            session.commit()
            
            return f"Set logged: {weight} lbs x {reps} reps"
        
        except Exception as e:
            session.rollback()
            return f"Error: {str(e)}"
    return ""