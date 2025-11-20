import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
HOST = os.getenv("HOST")
DATABASE = os.getenv("DATABASE")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")

def init_db():
    """
        Create the database if it does not exist yet.
        Initialize the tables.
        Wipe the log.
        Initliazize the muscle groups by adding key exercises.
    """
    create_db = """CREATE DATABASE IF NOT EXISTS workoutDB"""
    create_exercises_table = """CREATE TABLE IF NOT EXISTS exercises (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        muscle_group VARCHAR(100),
        equipment VARCHAR(100),
        UNIQUE (name, muscle_group, equipment)
        );"""
    create_workouts_table = """CREATE TABLE IF NOT EXISTS workouts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE NOT NULL,
        notes TEXT,
        duration_minutes INT
        );"""
    create_sets_table = """CREATE TABLE IF NOT EXISTS sets (
        workout_id INT NOT NULL,
        exercise_id INT NOT NULL,
        set_order INT NOT NULL,
        reps INT NOT NULL,
        weight DECIMAL(6,2),
        rpe DECIMAL(3,1),
        FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
        FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE RESTRICT,
        PRIMARY KEY (workout_id, exercise_id, set_order)
        );"""
    
    log(f"Initializing Database: {datetime.now().replace(microsecond=0)}", overwrite=True) # overwrite, begin new logfile

    execute_query(create_db)
    execute_query(create_exercises_table)
    execute_query(create_workouts_table)
    execute_query(create_sets_table)

    log("Tables Successfully Initialized")
    
    log("Initializing Muscle Groups Now...")

    new_exercise(name="Bench Press", description="The Classic Bench Press", muscle_group="Chest", equipment="Barbell")
    new_exercise(name="Lat Pulldown", description="The Classic Lat Pulldown", muscle_group="Back", equipment="Cable")
    new_exercise(name="Bicep Curl", description="The Classic Bicep Curl", muscle_group="Biceps", equipment="Dumbbell")
    new_exercise(name="Tricep Pulldown", description="The Classic Tricep Pulldown", muscle_group="Triceps", equipment="Cable")
    new_exercise(name="Leg Press", description="The Classic Leg Press", muscle_group="Legs", equipment="Machine")
    new_exercise(name="Military Press", description="The Classic Military Press", muscle_group="Shoulders", equipment="Smith Machine")
    new_exercise(name="Crunch", description="The Classic Ab Crunch", muscle_group="Abdominals", equipment="Bodyweight")


    log("Muscle Groups Successfully Initialized")

    log("------------------Database Successfully Initialized---------------------")

def establish_mysqlDB_connection():
    """
        Creates the connection to the MySQL Database.

        RETURNS
        -------
        connection
            The database connection object, if it was able to establish a connection.
            Check that the .env file data is correct or ping the MariaDB server if it returns a NoneType.
    """

    connection = mysql.connector.connect(
        host=HOST,
        database=DATABASE,
        user=USER,
        password=PASSWORD
    )
    if connection.is_connected():
        return connection
    else:
        log(f"{datetime.now().replace(microsecond=0)} - Error occured when attempting to establish a connection to the MariaDB Server. Check mariadb_config file or status of MariaDB server.")
        return False

def execute_query(query: str, input_params=None):
    """
        Execute a query on the database, uses the helper method above to connect to the DB.
        One issue with this format is that is creates a connection EVERY query, not sure of a better way to structure this.
        Could look into connection pooling later, but this app usage is usually:
            > Open > Input Set > Close (also I am the only user, so very low traffic)
        
        PARAMETERS
        ----------
        (query : str)
            - The SQL query for the database, in str() format. Easiest way to format is using the triple " to turn it into a docstring and use that.
        (input_params : Sequence[MySqlConvertibleType] || Dict[str:MySQLConvertibleType])
            - This is for the parameters for during an INSERT operation. Not sure still exactly how this typing works, but hovering over .execute() displays this.
            - My guess is mysql-connector object from an input list. Still working on understanding this datatype, but it does work as intended.
        
        RETURNS
        --------
        The result of:  cursor.fetchall()
            - This is a list of tuples from the executed SQL query. Looks like:
                [
                    {'name': 'bench press', 'muscle_group': 'chest'},
                    {'name': 'lat pulldown', 'muscle_group': 'back'}
                ]
    """

    connection = establish_mysqlDB_connection()

    if connection is not False:
        cursor = connection.cursor(dictionary=True, buffered=True)

        try:
            # check if we are querying with SELECT first -- need to know whether to start a transaction or not
            if query.split(" ")[0].strip() == "SELECT":
                cursor.execute(query)
                result = cursor.fetchall()
                return result
            else:
                connection.start_transaction()
                cursor.execute(query, params=input_params)
                connection.commit()
        
        # if an error occurred, we want to log it and rollback
        except Error as e:
            current_time = datetime.now().replace(microsecond=0)
            error_string = "default error string, if you see this then check the error log because an error happened but was not a normally-handled error"

            if str(e).startswith("1062 (23000): Duplicate entry"):
                error_string = f"{current_time}\t\t\t{e}\n\nDuplication Warning from Query:\n{query} with Input Parameters:\n{input_params}"
                log(error_string)

            elif query.startswith("INSERT INTO `exercises`"):
                error_string = f"{current_time}\t\t\t{e}\n\nError when attempting to INSERT INTO `exercises` table with input paramters:\n{input_params}"
                log(error_string)

            elif query.startswith("INSERT INTO `sets`"):
                error_string = f"{current_time}\t\t\t{e}\n\nError when attempting to INSERT INTO `sets` table with input paramters:\n{input_params}"
                log(error_string)

            elif query.startswith("INSERT INTO `workouts`"):
                error_string = f"{current_time}\t\t\t{e}\n\nError when attempting to INSERT INTO `exercises` table with input paramters:\n{input_params}"
                log(error_string)

            else:
                error_string = f"{current_time}\t\t\t{e}\n\nOther Error with Query: {query} and Input Parameters: {input_params}.\nError Returned: {e}"
                log(error_string)
        
            connection.rollback()
            return error_string
        
        # regardless of outcome, want to close the cursor and connection. Google says finally block runs even if you return within except block as well
        finally:
            cursor.close()
            connection.close()

    else:
        current_time = datetime.now().replace(microsecond=0)
        log(f"{current_time} - Error Executing Query, Connection returned was of NoneType")

def new_exercise(name: str, description: str, muscle_group: str, equipment: str):
    """
    Execute a query on the database to create a new exercise listing within the `exercises` table. First, check if exercise is already in DB.
    
    PARAMETERS
    ----------
    (name : str)
        MANDATORY. The name of the exercise
    (description : str)
        OPTIONAL. Text type descriptor of the exercise. 
    (muscle_group : str)
        MANDATORY. The muscle group for the new exercise. Maybe add sub muscle groups later? (rear delt, front delt, etc.)
    (equipment : str)
        MANDATORY. What is the main equipment needed for this new exercise?
    
    RETURNS
    --------
    Boolean. True if successfully executed the query, False if failed.
    """
    
    duplicate_exercise = execute_query(f"SELECT `exercises`.name, `exercises`.muscle_group, `exercises`.equipment FROM `exercises` WHERE `exercises`.name = '{name}' AND `exercises`.muscle_group = '{muscle_group}' AND `exercises`.equipment = '{equipment}'")
    if duplicate_exercise is not None and len(duplicate_exercise) > 0:
        return "Exercise is already in the database."
    else:
        new_exercise = """INSERT INTO `exercises` (name, description, muscle_group, equipment) VALUES (%s, %s, %s, %s)"""
        input_parameters = (name, description, muscle_group, equipment)
        execute_query(query=new_exercise, input_params=input_parameters)
        return f"New exercise added: {name}.\nMuscle Group: {muscle_group}.\nEquipment: {equipment}."

def new_workout(date) -> bool:
    """
    Execute a query on the database to create a new workout within the `workouts` table.
    Right now, this happens during logging a new set (no need to manually "start" a workout, happens automatically).
    
    PARAMETERS
    ----------
    (date : str)
        MANDATORY. The date of the workout in 'YYYY-MM-DD' format.
    
    RETURNS
    --------
    Boolean. True if successfully executed the query, False if failed.
    """
    
    new_workout = """INSERT INTO `workouts` (date) VALUE (%s)"""
    input_parameters = [date]
    execute_query(query=new_workout, input_params=input_parameters)

def new_set(workout_id: int, exercise_id: int, set_number: int, reps: int, weight: float, rpe: float=0):
    """
    Execute a query on the database to create a new `set` record within the `sets` table.
    
    PARAMETERS
    ----------
    (workout_id : str)
        MANDATORY. The workout ID foreign key from the `workouts` table. This links the set to a specific workout, used for grouping sets together.
        ATM, a workout is just the current date, but could be expanded later to include more metadata (duration, notes, etc. [these two already exist in the table]).
    (exercise_id : str)
        MANDATORY. The exercise ID foreign key from the `exercises` table. This links the set to a specific exercise.
    (set_number : str)
        MANDATORY. The number / order of the set within the workout for that exercise.
    (reps : str)
        MANDATORY. The number of reps completed for this set.
    (weight : str)
        MANDATORY. The weight used for this set. FULL DECIMAL SUPPORTED for converting between KGS and LBS (e.g., 135.50).
        Right now, no unit tracking, just assumes LBS for now. Also, instead of specifying drop sets or other advanced set types, just log them as separate sets.
    (rpe : str)
        OPTIONAL. The RPE (Rate of Perceived Exertion) for that set. Defaults to 0 because I usually do not log RPE. Also have not added functionality to change this yet, this is very far down on my list of things to implement.
    
    RETURNS
    --------
    Boolean. True if successfully executed the query, False if failed.
    """
    
    new_set = """INSERT INTO `sets` (workout_id, exercise_id, set_number, reps, weight, rpe) VALUES (%s, %s, %s, %s, %s, %s)"""
    input_parameters = (workout_id, exercise_id, set_number, reps, weight, rpe)

    execute_query(query=new_set, input_params=input_parameters)

def log(log_entry: str, overwrite: bool=False):
    """
        Making this to help with the amount of logging I added, too much copy paste so this will just handle the logging.

        PARAMETERS
        -----------
        (log_entry : str)
            The string to output into the log file.
        (overwrite: bool)
            Boolean for whether to overwrite the logfile instead of appending (default=appending)
    """
    if overwrite:
        with open("logfile.txt", "w") as logfile:
            logfile.write("-" * 100)
            logfile.write("\n")
            logfile.write(f"{log_entry}")
            logfile.write("\n")
            logfile.write("-" * 100)
    else:
        with open("logfile.txt", "a") as logfile:
                logfile.write("-" * 100)
                logfile.write("\n")
                logfile.write(f"{log_entry}")
                logfile.write("\n")
                logfile.write("-" * 100)
