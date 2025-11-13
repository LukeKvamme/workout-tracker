import mysql.connector
from mysql.connector import Error
from datetime import datetime
from mariadb_config import HOST, DATABASE, USER, PASSWORD

HOST = HOST
DATABASE = DATABASE
USER = USER
PASSWORD = PASSWORD

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
        id INT AUTO_INCREMENT PRIMARY KEY,
        workout_id INT NOT NULL,
        exercise_id INT NOT NULL,
        set_order INT NOT NULL,
        reps INT NOT NULL,
        weight DECIMAL(6,2),
        rpe DECIMAL(3,1),
        FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
        FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE RESTRICT
        );"""
    with open("logfile.txt", "w") as logfile:
        logfile.write(f"Initializing Database: {datetime.now().replace(microsecond=0)}\n")

    execute_query(create_db)
    execute_query(create_exercises_table)
    execute_query(create_workouts_table)
    execute_query(create_sets_table)

    with open("logfile.txt", "a") as logfile:
        logfile.write("-" * 80)
        logfile.write(f"\nTables Successfully Initialized\n")
        logfile.write("-" * 80)
        logfile.write("\nInitializing Muscle Groups\n")
    

    new_exercise(name="Bench Press", description="The Classic Bench Press", muscle_group="Chest", equipment="Barbell")
    new_exercise(name="Lat Pulldown", description="The Classic Lat Pulldown", muscle_group="Back", equipment="Cable")
    new_exercise(name="Bicep Curl", description="The Classic Bicep Curl", muscle_group="Biceps", equipment="Dumbbell")
    new_exercise(name="Tricep Pulldown", description="The Classic Tricep Pulldown", muscle_group="Triceps", equipment="Cable")
    new_exercise(name="Leg Press", description="The Classic Leg Press", muscle_group="Legs", equipment="Machine")
    new_exercise(name="Military Press", description="The Classic Military Press", muscle_group="Shoulders", equipment="Smith Machine")

    with open("logfile.txt", "a") as logfile:
        logfile.write("-" * 80)
        logfile.write(f"\nMuscle Groups Successfully Initialized\n")

    with open("logfile.txt", "a") as logfile:
        logfile.write("=" * 80)
        logfile.write(f"\nDatabase Successfully Initialized!\n")
        logfile.write("=" * 80)

def establish_mysqlDB_connection():
    """
        Creates the connection to the MySQL Database.

        RETURNS
        -------
        connection
            The database connection object, if it was able to establish a connection.
            Check the mariadb_config.py data is correct or MariaDB server if it returns a NoneType.
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
        with open("logfile.txt", 'a') as logfile:
            logfile.write(f"\n{datetime.now().replace(microsecond=0)} - Error occured when attempting to establish a connection to the MariaDB Server. Check mariadb_config file or status of MariaDB server.")
            logfile.write("\n")
            logfile.write("-" * 80)
        return False

def execute_query(query: str, input_params=None):
    """
        Execute a query on the database, uses the helper method above to connect to the DB.
        One issue with this format is that is creates a connection EVERY query, not sure of a better way to structure this.
        Could look into connection pooling later, but this app usage is usually:
            > Open > Input Set > Close
        
        PARAMETERS
        ----------
        (query : str)
            - The SQL query for the database, in str() format. Easiest way to format is using the triple " to turn it into a docstring and use that.
        (input_params : Sequence[MySqlConvertibleType] || Dict[str:MySQLConvertibleType])
            - This is for the parameters for during an INSERT operation. Not sure still exactly how this typing works, but hovering over .execute() displays this.
            - My guess is mysql-connector object from an input list. Still working on this part.
        
        RETURNS
        --------
        The result of:  cursor.fetchall()
            - This is a list of tuples from the executed SQL query. Looks like:
                [
                    (thing1, thing2, thing3),
                    (thing4, thing5, thing6)
                ]
    """

    connection = establish_mysqlDB_connection()

    if connection is not False:
        cursor = connection.cursor(dictionary=True, buffered=True)

        try:
            # check if we are querying first -- need to know whether to start a transaction or not
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
            with open("logfile.txt", "a") as logfile:
                logfile.write(f"\n{datetime.now().replace(microsecond=0)} - Error executing SQL query: {query}\nError Returned:{e}")
                logfile.write("\n")
                logfile.write("-" * 80)
            connection.rollback()
        
        # regardless of outcome, want to close the cursor and connection
        finally:
            cursor.close()
            connection.close()

    else:
        with open("logfile.txt", "a") as logfile:
                logfile.write(f"\n{datetime.now().replace(microsecond=0)} - Error Executing Query, Connection returned was of NoneType")
                logfile.write("\n")
                logfile.write("-" * 80)
        return False

def new_exercise(name: str, description: str, muscle_group: str, equipment: str) -> bool:
    """
    Execute a query on the database to create a new exercise listing within the `exercise` table.
    
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
    
    new_exercise = """INSERT INTO `exercises` (name, description, muscle_group, equipment) VALUES (%s, %s, %s, %s)"""
    input_parameters = (name, description, muscle_group, equipment)

    error_status = execute_query(query=new_exercise, input_params=input_parameters)

    if not error_status:
        with open("logfile.txt", "a") as logfile:
            logfile.write(f"\nSuccessfully inserted new exercise > {name} <\n")
            logfile.write("-" * 80)
        return True
    else:
        with open("logfile.txt", "a") as logfile:
            logfile.write(f"\n{datetime.now().replace(microsecond=0)} - Error when attempting to INSERT INTO `exercises` table with input paramters: {input_parameters}")
            logfile.write("-" * 80)

def new_workout(date) -> bool:
    """
    Execute a query on the database to create a new exercise listing within the `exercise` table.
    
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
    
    new_workout = """INSERT INTO `workouts` (date) VALUE (%s)"""
    params = [date]
    error_status = execute_query(query=new_workout, input_params=params)

    if not error_status:
        with open("logfile.txt", "a") as logfile:
            logfile.write(f"\nNew Workout Started > {date} <\n")
            logfile.write("-" * 80)
        return True
    else:
        with open("logfile.txt", "a") as logfile:
            logfile.write(f"\n{datetime.now().replace(microsecond=0)} - Error when attempting to INSERT INTO `exercises` table with input paramters: {input_parameters}")
            logfile.write("-" * 80)

def new_set(workout_id: int, exercise_id: int, set_number: int, reps: int, weight: float, rpe: float=0) -> bool:
    """
    Execute a query on the database to create a new exercise listing within the `exercise` table.
    
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
    
    new_set = """INSERT INTO `sets` (workout_id, exercise_id, set_order, reps, weight, rpe) VALUES (%s, %s, %s, %s, %s, %s)"""
    input_parameters = (workout_id, exercise_id, set_number, reps, weight, rpe)

    error_status = execute_query(query=new_set, input_params=input_parameters)

    if not error_status:
        with open("logfile.txt", "a") as logfile:
            logfile.write(f"\nSuccessfully inserted new set > {weight}lbs x {reps} <\n")
            logfile.write("-" * 80)
        return True
    else:
        with open("logfile.txt", "a") as logfile:
            logfile.write(f"\n{datetime.now().replace(microsecond=0)} - Error when attempting to INSERT INTO `exercises` table with input paramters: {input_parameters}")
            logfile.write("-" * 80)
