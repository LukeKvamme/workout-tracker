from dash import Dash, html, dcc, Input, Output, State, callback, callback_context
import dash
from datetime import datetime, date
from database import execute_query, new_workout, new_set

dash.register_page(__name__, path='/log-set')


# get exercises for dropdown. Dash needs {'label': 'abc', 'value': 'xyz'} formatting for dropdowns
exercise_options = execute_query("""SELECT * FROM `exercises`""")
exercises_list = []
for exercise in exercise_options:
    exercise_dict = {}
    exercise_dict['label'] = f"{exercise["muscle_group"]} {exercise["equipment"]} {exercise["name"]}"
    exercise_dict['value'] = exercise["id"]
    exercises_list.append(exercise_dict)

# sort exercises alphabetically by the 'label' value (muscle_group is first so this sorts exercises by muscles > equipment > name)
sorted_exercises = sorted(exercises_list, key=lambda x: x['label'])

layout = html.Div([
    html.H1(f"{datetime.now().date()}",
            style={
                'textAlign': 'center', 
                'marginBottom': '20px', 
                'color': '#333', 
                'font-family': 'Arial, sans-serif',
                'font-weight': 'bold',
                'borderBottom': '2px solid #000',
                'paddingBottom': '10px'}
    ),
    
    dcc.Dropdown(
        id='exercise-dropdown',
        options=sorted_exercises,
        placeholder="Select Exercise",
        style={
            'width': '100%', 
            'marginBottom': '5px',
            'padding': '8px',
            'fontSize': '16px',
            'align': 'center'
            }
    ),
    
    dcc.Input(
        id='weight-input', 
        type='number', 
        placeholder='Weight (lbs)',
        style={
            'width': '97%', 
            'marginBottom': '15px',
            'padding': '8px',
            'fontSize': '16px'
            }
    ),
    dcc.Input(
        id='reps-input', 
        type='number', 
        placeholder='Reps',
        style={
            'width': '97%', 
            'marginBottom': '15px',
            'padding': '8px',
            'fontSize': '16px'
            }
    ),
    
    html.Button('Log Set', 
                id='submit-button',
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

    html.Div(id='set-output-message')
])


@callback(
    Output('set-output-message', 'children'),
    Input('submit-button', 'n_clicks'),
    State('exercise-dropdown', 'value'),
    State('weight-input', 'value'),
    State('reps-input', 'value'),
    # State('set-number-input', 'value'),
    prevent_initial_call=True
)
def log_workout_set(n_clicks, exercise_id, weight, reps):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if not all([exercise_id, weight, reps]):
        return "Please fill in all required fields"
    
    if triggered_id == 'submit-button':
        try:
            workout_id = execute_query(f"""SELECT id, date FROM `workouts` ORDER BY date DESC LIMIT 1""")
            today = date.today()

            if workout_id[0]["date"] != today:
                new_workout(date=today)
                workout_id = execute_query(f"""SELECT id, date FROM `workouts` ORDER BY date DESC LIMIT 1""")

            set_number_tuple = execute_query(f"""SELECT `sets`.set_number FROM `sets` WHERE `sets`.workout_id = {workout_id[0]["id"]} AND `sets`.exercise_id = {exercise_id}""")
            if set_number_tuple is None or len(set_number_tuple) < 1:
                set_number = 1
            else:
                set_number = int(set_number_tuple[-1]["set_number"]) + 1
            
            new_set(workout_id=workout_id[0]["id"], exercise_id=exercise_id, weight=weight, reps=reps, set_number=set_number)
            
            exercise_name = execute_query(f"""SELECT name FROM `exercises` WHERE id = {exercise_id}""")
            return f"Set #{set_number} logged: {exercise_name[0]['name']} - {weight} lbs x {reps} reps. Weight just lifted: {weight * reps} lbs."
        
        except Exception as e:
            return f"Error: {str(e)}"

    return "This was not supposed to be returned, if you see this check the log_workout_set callback"