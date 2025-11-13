from dash import Dash, html, dcc, Input, Output, State, callback, callback_context
import dash
from datetime import datetime, date
from database import execute_query, new_workout, new_set

dash.register_page(__name__)


# get exercises for dropdown
exercise_options = execute_query("""SELECT * FROM `exercises`""")
exercises_list = []
for exercise in exercise_options:
    exercise_dict = {}
    exercise_dict['label'] = f"{exercise["muscle_group"]} {exercise["equipment"]} {exercise["name"]}"
    exercise_dict['value'] = exercise["id"]
    exercises_list.append(exercise_dict)


layout = html.Div([
    html.H2(id='workout-output-message'),
    html.Button('Begin New Workout', id='workout-button', n_clicks=0),
    html.H2("Log Workout Set"),
    
    dcc.Dropdown(
        id='exercise-dropdown',
        options=exercises_list,
        placeholder="Select Exercise"
    ),
    
    dcc.Input(id='weight-input', type='number', placeholder='Weight (lbs)'),
    dcc.Input(id='reps-input', type='number', placeholder='Reps'),
    dcc.Input(id='set-number-input', type='number', placeholder='Set Number'),
    
    html.Button('Log Set', id='submit-button', n_clicks=0),
    html.Div(id='set-output-message')
])

@callback(
    Output('workout-output-message', 'children'),
    Input('workout-button', 'n_clicks'),
    prevent_initial_call=True
)
def begin_workout(n_clicks):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == 'workout-button':
        today = date.today()
        if execute_query(f"""SELECT date FROM `workouts` WHERE date = {today}"""):
            new_workout(date=today)
        return f"Today's Workout:\n{datetime.now().date()}"


@callback(
    Output('set-output-message', 'children'),
    Input('submit-button', 'n_clicks'),
    State('exercise-dropdown', 'value'),
    State('weight-input', 'value'),
    State('reps-input', 'value'),
    State('set-number-input', 'value'),
    prevent_initial_call=True
)
def log_workout_set(n_clicks, exercise_id, weight, reps, set_number):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if not all([exercise_id, weight, reps]):
        return "Please fill in all required fields"
    
    if triggered_id == 'submit-button':
        try:
            workout_id = execute_query(f"""SELECT id FROM `workouts` ORDER BY id DESC LIMIT 1""")
            new_set(workout_id=workout_id[0]["id"], exercise_id=exercise_id, weight=weight, reps=reps, set_number=set_number)
            return f"Set logged: {weight} lbs x {reps} reps"
        
        except Exception as e:

            return f"Error: {str(e)}"

    return ""