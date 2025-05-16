import os, json, app.user_config as user_config

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


##############################################################################################################################
#                                                                                                                            #
#                                                                                                                            #
#                                      DATABASE + APP CONFIGURATION                                                          #
#                                                                                                                            #
#                                                                                                                            #
##############################################################################################################################
db = SQLAlchemy()
DB_NAME = "workout_database.db"


def create_app():
    '''
    Initialize the workout tracker app
    '''
    app = Flask(__name__)

    basedir = os.path.abspath(os.path.dirname(__file__))
    databasedir = os.path.join(basedir, os.path.join("database", DB_NAME) )
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{databasedir}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = user_config.get_secret_key() # Encrypts cookies and session data, if this changes / random gen then user is logged out every time on startup
    db.init_app(app)

    # Import Blueprints
    from .views import views
    from .auth import auth
    # Register Blueprints; url_prefix defines how to access this blueprint (view the @route defined in the .py file)
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    create_database(app, databasedir)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' #name of template > name of function
    login_manager.init_app(app) # tell login manager which app we are using

    from .models import User

    @login_manager.user_loader # references user by their id ...... idk?
    def load_user(id):
        return User.query.get(int(id)) # works similar to filter by, but looks for primary key, telling flask which user we are looking for


    return app


def create_database(app, databasedir):
    '''
    Initialize the database if it does not exist
    '''
    if not os.path.exists(databasedir):
        with app.app_context():
            db.create_all()
            muscles_initial_load(os.path.join(os.path.join("app", "static"), "muscles.json"))
            exercises_initial_load(os.path.join(os.path.join("app", "static"), "exercises.json"))
    
    # Verify that the tables were all created successfully
    with app.app_context():
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print("Tables created:", tables)

def muscles_initial_load(json_file_path):
    """
    Import muscles from a JSON file into the database
    """
    from .models import PrimaryMuscle, SecondaryMuscle

    # Read the JSON file
    with open(json_file_path, 'r') as f:
        muscle_data = json.load(f)
    
    # Track stats
    imported = 0
    skipped = 0

    for muscle in muscle_data:
        PM_existing = PrimaryMuscle.query.filter_by(muscle=muscle).first()
        SM_existing = SecondaryMuscle.query.filter_by(muscle=muscle).first()
        
        # Muscle already in both? Skip
        if PM_existing and SM_existing:
            print(f"Skipping {muscle} - already exists")
            skipped += 1
            continue
        
        # Muscle in Primary but not Secondary? Create new Secondary
        elif PM_existing and not SM_existing:
            new_secondary_muscle = SecondaryMuscle(
                muscle = muscle
            )
            db.session.add(new_secondary_muscle)

        # Muscle in Secondary but not Primary? Create new Primary
        elif SM_existing and not PM_existing:
            new_primary_muscle = PrimaryMuscle(
                muscle = muscle
            )
            db.session.add(new_primary_muscle)
        
        # else -- Muscle is NOT in Primary OR Secondary, so add it to both
        else:
            new_primary_muscle = PrimaryMuscle(
                muscle = muscle
            )
            new_secondary_muscle = SecondaryMuscle(
                muscle = muscle
            )

            db.session.add(new_primary_muscle)
            db.session.add(new_secondary_muscle)
    
        imported += 1
    
    # Commit all changes
    db.session.commit()
    print(f"\nImport complete: {imported} added, {skipped} skipped")

def exercises_initial_load(json_file_path):
    """
    Import exercises from a JSON file into the database
    """
    from .models import Exercise, PrimaryMuscle, SecondaryMuscle, InstructionStep
    
    # Read the JSON file
    with open(json_file_path, 'r') as f:
        exercises_data = json.load(f)

    
    # Track stats
    imported = 0
    skipped = 0
    
    # Process each exercise
    for exercise_data in exercises_data:
        # Check if exercise already exists
        existing = Exercise.query.filter_by(name=exercise_data['name']).first()
        
        if existing:
            print(f"Skipping {exercise_data['name']} - already exists")
            skipped += 1
            continue

        # Create the new exercise
        new_exercise = Exercise(
            name = exercise_data.get("name"),
            force = exercise_data.get("force"),
            level = exercise_data.get("level"),
            mechanic = exercise_data.get("mechanic"),
            equipment = exercise_data.get("equipment"),
            category = exercise_data.get("category")
        )
        db.session.add(new_exercise)
        db.session.flush()

        for primary_muscle in exercise_data.get('primaryMuscles'):
            muscle = PrimaryMuscle.query.filter_by(muscle=primary_muscle).first()
            new_exercise.primary_muscles.append(muscle)

        for secondary_muscle in exercise_data.get('secondaryMuscles'):
            muscle = SecondaryMuscle.query.filter_by(muscle=secondary_muscle).first()
            new_exercise.secondary_muscles.append(muscle)


         # Loop through the instructions of the new exercise, create a new instruction step for each instruction in the InstructionStep table
        step_count = 1
        for instruction_step in exercise_data.get("instructions"):
            new_instruction_step = InstructionStep(
                exercise_id = new_exercise.id,
                step_number = step_count,
                instruction_step = instruction_step
            )
            db.session.add(new_instruction_step)
            step_count += 1
        
        imported += 1
 
    # Commit all changes
    db.session.commit()
    print(f"\nImport complete: {imported} added, {skipped} skipped")


