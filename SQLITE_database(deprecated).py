from sqlalchemy import Column, ForeignKey, Integer, String, Text, Float, DateTime, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

"""
    Create the engine, Session, Base at module-level instead of a Database class:
        This is a small app for myself, so this is simple and works fine.
    This will create three singletons:
        Engine
        Session
        Base
    Engine is a Singleton:
        This creates one connection to the Database, which is then later used to bind the Session factory and create the tables within.
    Session is actually a Singleton Factory:
        Session has an __call__ method (I had never heard of this before now so I am documenting this for later lol)
        This __call__ method returns a new Session everytime it is called, meaning that session = Session() in each page will actually return a new Session.
        So this Session factory instantiates a new Session object whenever Session() is called (which calls the Factory's __call__ method)
            More about __call__:
                You can call a class by doing Class() OR Class.__call__().
                THis is possible because not only are *functions* callable in Python, but so too are **Classes**.
                Any object with __call__() is actuall 'callable'.
                Weird.
    Base is a Singleton because:
        Base = declarative_base() creates a Singleton 'Base' object.
        Then, when declaring all of the database tables as the 'class Set(Base):', all these model classes inherit from the SAME BASE.
        Which then makes it so that Base.metadata holds the metadata for ALL of the tables, so Base.metadata.create_all(Engine) will
            create ALL the tables that inherit from Base using that metadata and the connected Engine Singleton object.
"""

Engine = create_engine('sqlite:///workout_database.db') 

Session = sessionmaker(bind=Engine) # Binds the singleton-factory Session to the singleton Engine

Base = declarative_base()

def init_db():
    """
        Helper function to create all of the tables (if they do not all already exist, otherwise just connects), called when app first initializes.
    """
    Base.metadata.create_all(Engine)

"""
    OK, the database models are below. They inherit from the Base Singleton.
        Exercise - Catalogue of the exercises
        Workout - Workout is a workout session container for 1 workout, relation to the Sets via a FK in the Set table
        Set - 1 Set within a workout. Two FK's - WorkoutID and ExerciseID
    
    The back_populate is weird and is apparently just for easier Python--it automatically joins the tables.
        Related to MySQL, it is like automatically having a WHERE Sets.ExerciseID = Exercise.ExerciseID when joining tables.
        Can also make it more concise by using just a 'backref' in 1 table, but the back_populates it weird enough.
"""

class Exercise(Base):
    __tablename__ = 'exercise'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50))
    equipment = Column(String(50))
    notes = Column(Text)
    
    sets = relationship('Set', back_populates='exercise')

class Workout(Base):
    __tablename__ = 'workout'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    name = Column(String(100))
    duration_minutes = Column(Integer)
    notes = Column(Text)
    
    sets = relationship('Set', back_populates='workout', cascade='all, delete-orphan')

class Set(Base):
    __tablename__ = 'set'
    
    id = Column(Integer, primary_key=True)
    workout_id = Column(Integer, ForeignKey('workout.id'), nullable=False)
    exercise_id = Column(Integer, ForeignKey('exercise.id'), nullable=False)
    set_number = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    rpe = Column(Integer)
    notes = Column(String(200))
    
    workout = relationship('Workout', back_populates='sets')
    exercise = relationship('Exercise', back_populates='sets')