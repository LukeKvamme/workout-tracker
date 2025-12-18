from dash import Dash, html, dcc, Input, Output, State, callback, callback_context
import dash
from datetime import datetime, date
from database import execute_query, new_workout, new_set, establish_mysqlDB_connection

dash.register_page(__name__, path='/log-set')




def update_on_page_load():
    """
        By default, Dash loads the layout on first page load and then stores in memory.
        This means that you cannot refresh it with new information from the database.

        If you create_new_exercise >> try to log a set for that new exercise, you would not
        see it in the dropdown for exercise selection because the new db info has not been populated.
        
        This is a way to force Dash to load the page on every visit to the page, by establishing a new connection, re-querying the DB
        for all the exercises, and then returning the layout.
        as a function.
    """
    establish_mysqlDB_connection() # refresh connection

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


    layout = html.Div([ html.Div([
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
                },
            n_submit=0
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
                    n_clicks=0)
        ]),
        dcc.Store(id='logged-sets-store'),
        html.Div(id='set-output-message'),
        html.Div(id='logged-sets-div', 
                 style={
                        'marginTop': '30px',
                        'padding': '10px',
                        'border': '1px solid #ddd',
                        'border-radius': '5px',
                        'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.1)',
                        'backgroundColor': '#f9f9f9',
                        'font-family': 'Arial, sans-serif'
                     })
    ])

    return layout

layout = update_on_page_load











@callback(
    [Output('set-output-message', 'value'),
     Output('logged-sets-store', 'data'),
     Output('weight-input', 'value'),
     Output('reps-input', 'value')],
    [Input('submit-button', 'n_clicks'),
     Input('reps-input', 'n_submit')],
    State('exercise-dropdown', 'value'),
    State('weight-input', 'value'),
    State('reps-input', 'value'),
    prevent_initial_call=True
)
def log_workout_set(n_clicks, n_submit, exercise_id, weight, reps):
    if not all([exercise_id, weight, reps]):
        return "Please fill in all required fields"
    
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == 'submit-button' or 'reps-input':
        try:
            workout_id_tup = execute_query(f"""SELECT id, date FROM `workouts` ORDER BY date DESC LIMIT 1""")
            today = date.today()

            # if date != today --> create a new entry in `workouts`, return the workout_id from the new workout
            if workout_id_tup[0]["date"] != today:
                new_workout(date=today)
                workout_id_tup = execute_query(f"""SELECT id, date FROM `workouts` ORDER BY date DESC LIMIT 1""")
            
            # rather than copy-paste workout_id_tup[0]["id"] multiple times, just reassign it immediately
            workout_id = workout_id_tup[0]["id"]

            # autodetect set_number: find set_number for current workout_id and exercise_id. If None/len(tuple)<1 --> beginning new set, so set_number = 1
            set_number_tuple = execute_query(f"""SELECT `sets`.set_number FROM `sets` WHERE `sets`.workout_id = {workout_id} AND `sets`.exercise_id = {exercise_id}""")
            if set_number_tuple is None or len(set_number_tuple) < 1:
                set_number = 1
            else:
                set_number = int(set_number_tuple[-1]["set_number"]) + 1
            
            # now that we have  determined the workout_id and set_number --> actually log this new workout set
            new_set(workout_id=workout_id, exercise_id=exercise_id, weight=weight, reps=reps, set_number=set_number)
            
            set_PK_dict = {
                "workout_id": workout_id,
                "exercise_id": exercise_id,
                "set_number": set_number
            }
            
            return f"Successfully logged set #{set_number} for exercise ID {exercise_id}: {weight} lbs x {reps} reps.", set_PK_dict, None, None
        except Exception as e:
            return f"Error in the callback function when logging a new set: {str(e)}"

    return "How did we get here? << Check log set callback"

@callback(
    Output('logged-sets-div', 'children'),
    # State('workout-id-store', 'data'),
    Input('logged-sets-store', 'data'),
    prevent_initial_call=True # I think you could remove this part, then move all the workout_id logic to this callback and then have all prev sets load on page load (rn they all only load after logging a set)
)
def display_sets(set_PK_dict):
    if set_PK_dict is None:
        return "No sets logged yet today."
    workout_id = set_PK_dict['workout_id']
    exercise_id = set_PK_dict['exercise_id']
    set_number = set_PK_dict['set_number']

    # OK, next is to formulate the Div elements for below the set-logging form. Will need the exercise names, set #'s, weight, reps
    total_sets_tuple = execute_query(f"""SELECT e.name, e.equipment, s.set_number, s.weight, s.reps FROM sets s INNER JOIN exercises e ON s.exercise_id = e.id AND s.workout_id = {workout_id} ORDER BY e.name, s.set_number ASC""")
    sets_div_elements = []

    for index, value in enumerate(total_sets_tuple):
        sets_div_elements.append(
            html.Div(
                children=[
                    html.Br(),
                    html.H3(f"\t{value['equipment']} {value['name']}"),
                    html.P(f"\tSet #{value['set_number']} - {value['weight']}x{value['reps']}"),
                    html.P(f">>> {int(value['weight']) * int(value['reps'])} lbs.")
                ],
                style={
                    'padding': '10px',
                    'marginBottom': '10px',
                    'border': '1px solid #ccc',
                    'borderRadius': '5px',
                    'backgroundColor': '#fff',
                    'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.1)'
                }
            )
        )

    # set_tuple = execute_query(f"""SELECT e.name, s.set_number, s.weight, s.reps FROM sets s INNER JOIN exercises e ON s.exercise_id = e.id WHERE s.workout_id = {workout_id} AND s.exercise_id = {exercise_id} ORDER BY s.set_number ASC""")
    # sets_div_elements = []

    # for index, value in enumerate(set_tuple):
    #     sets_div_elements.append(
    #         html.Div(
    #             children=[
    #                 html.Br(),
    #                 html.H3(f"{value['name']}"),
    #                 html.P(f"\tSet #{value['set_number']} - {value['weight']}x{value['reps']}"),
    #                 html.P(f">>> {int(value['weight']) * int(value['reps'])} lbs.")
    #             ]
    #         )
    #     )

    return sets_div_elements
            