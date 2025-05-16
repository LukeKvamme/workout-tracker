from datetime import datetime
from sqlalchemy import func
from flask_login import UserMixin
from . import db

##############################################################################################################################
#                                                                                                                            #
#                                                                                                                            #
#                                            DATABASE MODELS                                                                 #
#                                                                                                                            #
#                                                                                                                            #
##############################################################################################################################
'''
    Models:
            Exercise                    \         Exercise       >>  1-Many  >> WorkoutEntry
            WorkoutSession    __________ \        WorkoutSession >>  1-Many  >> WorkoutEntry
            WorkoutEntry                 /        ExerciseSet    >>   1-1    >> WorkoutEntry
            ExerciseSet                 /
'''
# Create the many-many table associations between Exercise - Primary Muscle and Exercise - Secondary Muscle
association_exercise_primary_muscle = db.Table(
    'association_exercise_primary_muscle',
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercise.id'), primary_key=True),
    db.Column('muscle_id', db.Integer, db.ForeignKey('primary_muscle.id'), primary_key=True)
    )

association_exercise_secondary_muscle = db.Table(
    'association_exercise_secondary_muscle',
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercise.id'), primary_key=True),
    db.Column('muscle_id', db.Integer, db.ForeignKey('secondary_muscle.id'), primary_key=True)
    )

class Exercise(db.Model):
    """Represents a type of exercise"""
    __tablename__ = "exercise"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    force = db.Column(db.String(50))
    level = db.Column(db.String(50))
    mechanic = db.Column(db.String(50))
    equipment = db.Column(db.String(100))

    category = db.Column(db.String(50))

    # Tracking when the exercise was added
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Build the relationships (this took me way longer than it probably should have)
    primary_muscles = db.relationship(
        'PrimaryMuscle', 
        secondary='association_exercise_primary_muscle', 
        back_populates='exercises'
        )
    secondary_muscles = db.relationship(
        'SecondaryMuscle', 
        secondary='association_exercise_secondary_muscle',
        back_populates='exercises'
        )
    instructions = db.relationship(
        'InstructionStep', 
        back_populates='exercise',
        order_by="InstructionStep.step_number"
        )
    workout_entries = db.relationship(
        'WorkoutEntry', 
        back_populates='exercise'
        )
    
    def get_personal_best(self, metric='weight'):
        """Find the personal best for this exercise"""
        if metric == 'weight':
            return db.session.query(func.max(ExerciseSet.weight))\
                .join(WorkoutEntry)\
                .filter(WorkoutEntry.exercise_id == self.id)\
                .scalar()

class PrimaryMuscle(db.Model):
    """Represents the primary muscles used during an exercise"""
    __tablename__ = "primary_muscle"
    
    id = db.Column(db.Integer, primary_key=True)
    muscle = db.Column(db.String(50))

    exercises = db.relationship(
        'Exercise', 
        secondary='association_exercise_primary_muscle', 
        back_populates='primary_muscles'
        )

class SecondaryMuscle(db.Model):
    """Repesents the secondary muscles used during an exercise"""
    __tablename__ = "secondary_muscle"
    
    id = db.Column(db.Integer, primary_key=True)
    muscle = db.Column(db.String(50))

    exercises = db.relationship(
        'Exercise', 
        secondary='association_exercise_secondary_muscle',
        back_populates='secondary_muscles'
        )

class InstructionStep(db.Model):
    """Represents the instructions for how to perform the exercise"""
    __tablename__ = "instruction_step"
    
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    instruction_step = db.Column(db.String(250))

    exercise = db.relationship(
        'Exercise', 
        back_populates='instructions'
        )

class WorkoutEntry(db.Model):
    """Represents performing a specific exercise during a workout"""
    __tablename__ = "workout_entry"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('workout_session.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    order = db.Column(db.Integer)
    
    # warm-up sets separate from working sets
    is_warmup = db.Column(db.Boolean, default=False)
    
    session = db.relationship(
        'WorkoutSession',
        back_populates='entries'
        )
    exercise = db.relationship(
        'Exercise', 
        back_populates='workout_entries'
        )
    sets = db.relationship(
        'ExerciseSet', 
        back_populates='workout_entry', 
        cascade='all, delete-orphan', 
        order_by='ExerciseSet.set_number'
        )

class ExerciseSet(db.Model):
    """Represents a single set within an exercise"""
    __tablename__ = "exercise_set"

    id = db.Column(db.Integer, primary_key=True)
    workout_entry_id = db.Column(db.Integer, db.ForeignKey('workout_entry.id'), nullable=False)
    set_number = db.Column(db.Integer, nullable=False)
    
    # Strength training fields
    reps = db.Column(db.Integer)
    weight = db.Column(db.Float)
    
    # Cardio fields
    distance = db.Column(db.Float)
    duration_seconds = db.Column(db.Integer)
    
    # Additional tracking
    rest_seconds = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    rpe = db.Column(db.Integer)
    notes = db.Column(db.String(200))  # "Felt easy", "Form breakdown on last rep"
    
    workout_entry = db.relationship(
        'WorkoutEntry', 
        back_populates='sets'
        )
    
    def get_volume(self):
        """Calculate volume for this set"""
        if self.weight and self.reps:
            return self.weight * self.reps
        return 0
    
class WorkoutSession(db.Model):
    """Represents a single workout session"""
    __tablename__ = "workout_session"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text)

    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    duration_minutes = db.Column(db.Integer)
    status = db.Column(db.String(20), default='active')  # 'active', 'paused', 'completed'
    paused_at = db.Column(db.DateTime)
    paused_duration = db.Column(db.Integer, default=0)  # Total seconds paused
    
    workout_type = db.Column(db.String(100))  # 'Upper Body', 'Legs', 'Cardio', etc.
    
    entries = db.relationship(
        'WorkoutEntry', 
        back_populates='session', 
        cascade='all, delete-orphan', 
        order_by='WorkoutEntry.order'
        )
    user_session = db.relationship(
        "User",
        back_populates="workout_sessions"
    )
    
    def get_total_volume(self):
        """Calculate total volume (weight x reps) for the workout"""
        total = 0
        for entry in self.entries:
            for set_data in entry.sets:
                if set_data.weight and set_data.reps:
                    total += set_data.weight * set_data.reps
        return total
    
class User(db.Model, UserMixin):
    """Represents a user"""
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

    workout_sessions = db.relationship(
        "WorkoutSession",
        back_populates="user_session"
    )
