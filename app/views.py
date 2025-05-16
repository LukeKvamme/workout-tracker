import calendar
from flask_login import current_user, login_required
from .models import Exercise, ExerciseSet, PrimaryMuscle, SecondaryMuscle, WorkoutEntry, WorkoutSession
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from sqlalchemy.orm import joinedload
from collections import defaultdict
from datetime import datetime, timedelta
from sqlalchemy import desc, extract, func, text
from . import db


# Define this file as a Blueprint of the app ==> a bunch of URL's inside of it (the routes)
views = Blueprint('views', __name__)
from .models import association_exercise_primary_muscle
exercise_muscle_association = association_exercise_primary_muscle

# In a test route or script
@views.route('/test')
def test_relationships():
    exercise = Exercise.query.first()
    if exercise:
        print(f"Exercise: {exercise.name}")
        print(f"Primary muscles: {[m.muscle for m in exercise.primary_muscles]}")
        print(f"Secondary muscles: {[m.muscle for m in exercise.secondary_muscles]}")
    
    # Check association table directly
    result = db.session.execute(
        text("SELECT * FROM association_exercise_primary_muscle LIMIT 10")
    ).fetchall()
    print(f"Association table entries: {result}")
    
    return "Check console"

@views.route('/')
@views.route('/home')
@login_required
def home():
    # Get the last 3 completed workouts
    recent_workouts = WorkoutSession.query.filter_by(
        status='completed'
    ).order_by(
        WorkoutSession.date.desc()
    ).limit(3).all()
    
    # Calculate stats for each workout
    for workout in recent_workouts:
        # Get entries and exercises for this workout
        entries = WorkoutEntry.query.filter_by(session_id=workout.id).options(
            joinedload(WorkoutEntry.exercise),
            joinedload(WorkoutEntry.sets)
        ).all()
        
        # Calculate stats
        sets_count = sum(len(entry.sets) for entry in entries)
        exercises_count = len(entries)
        volume = sum(sum(s.weight * s.reps for s in entry.sets) for entry in entries)
        
        # Store stats
        workout.stats = {
            'sets': sets_count,
            'exercises': exercises_count,
            'volume': volume
        }
        
        # Get exercise details
        workout.exercises = []
        for entry in entries:
            workout.exercises.append({
                'name': entry.exercise.name,
                'set_count': len(entry.sets)
            })
    
    # Calculate overall stats
    
    # 1. Workouts this month
    now = datetime.now()
    first_day = datetime(now.year, now.month, 1)
    last_day = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
    
    workouts_this_month = WorkoutSession.query.filter(
        WorkoutSession.date >= first_day,
        WorkoutSession.date <= last_day,
        WorkoutSession.status == 'completed'
    ).count()
    
    # 2. Total volume (all time)
    # This query may need adjustment based on your exact schema
    total_volume = db.session.query(
        func.sum(ExerciseSet.weight * ExerciseSet.reps)
    ).join(
        WorkoutEntry, ExerciseSet.workout_entry_id == WorkoutEntry.id
    ).join(
        WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutSession.status == 'completed'
    ).scalar() or 0
    
    # 3. Workout streak
    # This is a simplistic approach - for a real app you'd need more logic
    workout_streak = calculate_workout_streak()
    
    stats = {
        'workouts_this_month': workouts_this_month,
        'total_volume': total_volume,
        'workout_streak': workout_streak
    }
    
    return render_template('home.html',
                          recent_workouts=recent_workouts,
                          stats=stats,
                          current_month=now.strftime('%B'),
                          user=current_user)

# Helper function to calculate workout streak
def calculate_workout_streak():
    """Calculate current workout streak (consecutive days)"""
    # Get all workout dates sorted by date descending
    workout_dates = [
        w.date.date() for w in WorkoutSession.query.filter_by(
            status='completed'
        ).order_by(WorkoutSession.date.desc()).all()
    ]
    
    if not workout_dates:
        return 0
    
    # Check if today has a workout
    today = datetime.now().date()
    streak = 0
    
    # If no workout today, check yesterday
    if today not in workout_dates:
        if (today - timedelta(days=1)) not in workout_dates:
            return 0  # Streak broken - no workout yesterday or today
        
        # Start counting from yesterday
        check_date = today - timedelta(days=1)
    else:
        # Start counting from today
        check_date = today
    
    # Count consecutive days
    while check_date in workout_dates:
        streak += 1
        check_date -= timedelta(days=1)
    
    return streak

# Route for all workouts
@views.route('/workouts')
@login_required
def all_workouts():
    # Placeholder - you can create a separate page that lists all workouts
    # For now, just redirect to home
    return redirect(url_for('views.home'))

@views.route('/stats')
def stats():
    # Get date range from query parameters or use defaults
    end_date = request.args.get('end_date', None)
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()
    
    start_date = request.args.get('start_date', None)
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        # Default to 3 months ago
        start_date = end_date - timedelta(days=90)
    
    # Format dates for template
    default_start = start_date.strftime('%Y-%m-%d')
    default_end = end_date.strftime('%Y-%m-%d')
    
    # Calculate overall stats within date range
    overall_stats = calculate_overall_stats(start_date, end_date)
    
    # Calculate time comparisons (current vs previous periods)
    comparisons = calculate_time_comparisons()
    
    # Prepare chart data
    volume_chart = prepare_volume_chart(start_date, end_date)
    muscle_chart = prepare_muscle_chart(start_date, end_date)
    frequency_chart = prepare_frequency_chart(start_date, end_date)
    top_exercises = prepare_top_exercises_chart(start_date, end_date)
    
    # Get all exercises with their stats
    all_exercises = get_all_exercises_with_stats()
    
    # Get all muscles with their stats
    all_muscles = get_all_muscles_with_stats()
    
    return render_template('stats.html',
                          default_start=default_start,
                          default_end=default_end,
                          overall_stats=overall_stats,
                          comparisons=comparisons,
                          volume_chart=volume_chart,
                          muscle_chart=muscle_chart,
                          frequency_chart=frequency_chart,
                          top_exercises=top_exercises,
                          all_exercises=all_exercises,
                          all_muscles=all_muscles,
                          user=current_user)

# API endpoint for exercise-specific stats
@views.route('/api/exercise-stats/<int:exercise_id>')
def exercise_stats_api(exercise_id):
    # Get the exercise
    exercise = Exercise.query.get_or_404(exercise_id)
    
    # Get all entries for this exercise
    entries = WorkoutEntry.query.filter(
        WorkoutEntry.exercise_id == exercise_id
    ).join(
        WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutSession.status == 'completed'
    ).options(
        joinedload(WorkoutEntry.sets)
    ).order_by(
        WorkoutSession.date.desc()
    ).all()
    
    # Calculate stats
    total_sets = sum(len(entry.sets) for entry in entries)
    total_reps = sum(sum(s.reps for s in entry.sets) for entry in entries)
    all_weights = [s.weight for entry in entries for s in entry.sets]
    max_weight = max(all_weights) if all_weights else 0
    total_volume = sum(s.weight * s.reps for entry in entries for s in entry.sets)
    
    # Prepare recent sets data
    recent_sets = []
    for entry in entries[:5]:  # Get the 5 most recent entries
        workout_date = entry.session.date.strftime('%b %d, %Y')
        for s in entry.sets:
            recent_sets.append({
                'date': workout_date,
                'set_number': s.set_number,
                'weight': s.weight,
                'reps': s.reps,
                'volume': int(s.weight * s.reps)
            })
    
    # Prepare chart data
    chart_data = prepare_exercise_progress_chart(exercise_id)
    
    return jsonify({
        'name': exercise.name,
        'total_sets': total_sets,
        'total_reps': total_reps,
        'max_weight': max_weight,
        'total_volume': int(total_volume),
        'sets': recent_sets,
        'chart': chart_data
    })

# API endpoint for muscle-specific stats
@views.route('/api/muscle-stats/<muscle_name>')
def muscle_stats_api(muscle_name):
    # Get all entries for exercises that target this muscle
    entries = WorkoutEntry.query.join(
        Exercise, WorkoutEntry.exercise_id == Exercise.id
    ).join(
        exercise_muscle_association, 
        Exercise.id == exercise_muscle_association.c.exercise_id
    ).join(
        PrimaryMuscle, 
        exercise_muscle_association.c.muscle_id == PrimaryMuscle.id
    ).join(
        WorkoutSession, 
        WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutSession.status == 'completed',
        PrimaryMuscle.muscle == muscle_name
    ).options(
        joinedload(WorkoutEntry.sets),
        joinedload(WorkoutEntry.exercise)
    ).all()
    
    # Calculate stats
    total_sets = sum(len(entry.sets) for entry in entries)
    total_reps = sum(sum(s.reps for s in entry.sets) for entry in entries)
    total_volume = sum(s.weight * s.reps for entry in entries for s in entry.sets)
    
    # Get max weight if relevant
    all_weights = [s.weight for entry in entries for s in entry.sets]
    max_weight = max(all_weights) if all_weights else None
    
    # Get stats by exercise
    exercise_stats = {}
    for entry in entries:
        exercise_name = entry.exercise.name
        if exercise_name not in exercise_stats:
            exercise_stats[exercise_name] = {
                'name': exercise_name,
                'total_sets': 0,
                'total_volume': 0,
                'max_weight': 0
            }
        
        exercise_stats[exercise_name]['total_sets'] += len(entry.sets)
        exercise_stats[exercise_name]['total_volume'] += sum(s.weight * s.reps for s in entry.sets)
        
        entry_max_weight = max([s.weight for s in entry.sets]) if entry.sets else 0
        exercise_stats[exercise_name]['max_weight'] = max(
            exercise_stats[exercise_name]['max_weight'], 
            entry_max_weight
        )
    
    # Prepare chart data - volume by day
    chart_data = prepare_muscle_volume_chart(muscle_name)
    
    return jsonify({
        'name': muscle_name,
        'total_sets': total_sets,
        'total_reps': total_reps,
        'max_weight': max_weight,
        'total_volume': int(total_volume),
        'exercises': list(exercise_stats.values()),
        'chart': chart_data
    })

# Helper functions
def calculate_overall_stats(start_date, end_date):
    """Calculate overall workout statistics within date range"""
    # Query for completed workouts in date range
    workouts = WorkoutSession.query.filter(
        WorkoutSession.date >= start_date,
        WorkoutSession.date <= end_date,
        WorkoutSession.status == 'completed'
    ).all()
    
    # Total workouts
    total_workouts = len(workouts)
    
    # Total workout time (hours)
    total_minutes = sum(w.duration_minutes or 0 for w in workouts)
    total_hours = round(total_minutes / 60, 1)
    
    # Get all entries and calculate sets, reps, volume
    entries = WorkoutEntry.query.join(
        WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutSession.date >= start_date,
        WorkoutSession.date <= end_date,
        WorkoutSession.status == 'completed'
    ).options(
        joinedload(WorkoutEntry.sets)
    ).all()
    
    total_sets = sum(len(entry.sets) for entry in entries)
    total_reps = sum(sum(s.reps for s in entry.sets) for entry in entries)
    total_volume = sum(s.weight * s.reps for entry in entries for s in entry.sets)
    
    # Max weight lifted
    all_weights = [s.weight for entry in entries for s in entry.sets]
    max_weight = max(all_weights) if all_weights else 0
    
    return {
        'total_workouts': total_workouts,
        'total_time': total_hours,
        'total_sets': total_sets,
        'total_reps': total_reps,
        'total_volume': total_volume,
        'max_weight': max_weight
    }

def calculate_time_comparisons():
    """Calculate comparisons between current and previous periods"""
    now = datetime.now()
    
    # Current week
    current_week_start = now - timedelta(days=now.weekday())
    current_week_start = datetime(current_week_start.year, current_week_start.month, current_week_start.day)
    previous_week_start = current_week_start - timedelta(days=7)
    
    current_week_workouts = count_workouts_in_period(current_week_start, now)
    previous_week_workouts = count_workouts_in_period(previous_week_start, current_week_start)
    
    current_week_volume = calculate_volume_in_period(current_week_start, now)
    previous_week_volume = calculate_volume_in_period(previous_week_start, current_week_start)
    
    # Calculate percentage changes
    week_workouts_change = calculate_percentage_change(previous_week_workouts, current_week_workouts)
    week_volume_change = calculate_percentage_change(previous_week_volume, current_week_volume)
    
    # Current month
    current_month_start = datetime(now.year, now.month, 1)
    if now.month == 1:
        previous_month_start = datetime(now.year - 1, 12, 1)
    else:
        previous_month_start = datetime(now.year, now.month - 1, 1)
    previous_month_end = current_month_start - timedelta(days=1)
    
    current_month_workouts = count_workouts_in_period(current_month_start, now)
    previous_month_workouts = count_workouts_in_period(previous_month_start, previous_month_end)
    
    current_month_volume = calculate_volume_in_period(current_month_start, now)
    previous_month_volume = calculate_volume_in_period(previous_month_start, previous_month_end)
    
    month_workouts_change = calculate_percentage_change(previous_month_workouts, current_month_workouts)
    month_volume_change = calculate_percentage_change(previous_month_volume, current_month_volume)
    
    # Current year
    current_year_start = datetime(now.year, 1, 1)
    previous_year_start = datetime(now.year - 1, 1, 1)
    previous_year_end = datetime(now.year - 1, 12, 31)
    
    current_year_workouts = count_workouts_in_period(current_year_start, now)
    previous_year_workouts = count_workouts_in_period(previous_year_start, previous_year_end)
    
    current_year_volume = calculate_volume_in_period(current_year_start, now)
    previous_year_volume = calculate_volume_in_period(previous_year_start, previous_year_end)
    
    year_workouts_change = calculate_percentage_change(previous_year_workouts, current_year_workouts)
    year_volume_change = calculate_percentage_change(previous_year_volume, current_year_volume)
    
    return {
        'current_week': {
            'workouts': current_week_workouts,
            'workouts_change': week_workouts_change,
            'volume': current_week_volume,
            'volume_change': week_volume_change
        },
        'current_month': {
            'workouts': current_month_workouts,
            'workouts_change': month_workouts_change,
            'volume': current_month_volume,
            'volume_change': month_volume_change
        },
        'current_year': {
            'workouts': current_year_workouts,
            'workouts_change': year_workouts_change,
            'volume': current_year_volume,
            'volume_change': year_volume_change
        }
    }

def count_workouts_in_period(start_date, end_date):
    """Count workouts within a time period"""
    return WorkoutSession.query.filter(
        WorkoutSession.date >= start_date,
        WorkoutSession.date <= end_date,
        WorkoutSession.status == 'completed'
    ).count()

def calculate_volume_in_period(start_date, end_date):
    """Calculate total volume lifted within a time period"""
    volume = db.session.query(
        func.sum(ExerciseSet.weight * ExerciseSet.reps)
    ).join(
        WorkoutEntry, ExerciseSet.workout_entry_id == WorkoutEntry.id
    ).join(
        WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutSession.date >= start_date,
        WorkoutSession.date <= end_date,
        WorkoutSession.status == 'completed'
    ).scalar()
    
    return volume or 0

def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0  # Avoid division by zero
    
    change = ((new_value - old_value) / old_value) * 100
    return round(change)

def prepare_volume_chart(start_date, end_date):
    """Prepare data for volume over time chart"""
    # Query for workout dates and volumes
    workout_volumes = db.session.query(
        WorkoutSession.date,
        func.sum(ExerciseSet.weight * ExerciseSet.reps).label('volume')
    ).join(
        WorkoutEntry, WorkoutSession.id == WorkoutEntry.session_id
    ).join(
        ExerciseSet, WorkoutEntry.id == ExerciseSet.workout_entry_id
    ).filter(
        WorkoutSession.date >= start_date,
        WorkoutSession.date <= end_date,
        WorkoutSession.status == 'completed'
    ).group_by(
        WorkoutSession.date
    ).order_by(
        WorkoutSession.date
    ).all()
    
    labels = [w.date.strftime('%b %d') for w in workout_volumes]
    data = [int(w.volume) for w in workout_volumes]
    
    return {'labels': labels, 'data': data}

def prepare_muscle_chart(start_date, end_date):
    """Prepare data for muscle groups chart"""
    # Query for primary muscles and their volume
    muscle_volumes = db.session.query(
        PrimaryMuscle.muscle,
        func.sum(ExerciseSet.weight * ExerciseSet.reps).label('volume')
    ).join(
        exercise_muscle_association, 
        PrimaryMuscle.id == exercise_muscle_association.c.muscle_id
    ).join(
        Exercise, 
        exercise_muscle_association.c.exercise_id == Exercise.id
    ).join(
        WorkoutEntry, 
        Exercise.id == WorkoutEntry.exercise_id
    ).join(
        ExerciseSet, 
        WorkoutEntry.id == ExerciseSet.workout_entry_id
    ).join(
        WorkoutSession, 
        WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutSession.date >= start_date,
        WorkoutSession.date <= end_date,
        WorkoutSession.status == 'completed'
    ).group_by(
        PrimaryMuscle.muscle
    ).order_by(
        desc('volume')
    ).limit(10).all()
    
    labels = [m.muscle for m in muscle_volumes]
    data = [int(m.volume) for m in muscle_volumes]
    
    return {'labels': labels, 'data': data}

def prepare_frequency_chart(start_date, end_date):
    """Prepare data for workout frequency by day of week"""
    # Count workouts by day of week
    day_counts = db.session.query(
        extract('dow', WorkoutSession.date).label('day_of_week'),
        func.count(WorkoutSession.id).label('count')
    ).filter(
        WorkoutSession.date >= start_date,
        WorkoutSession.date <= end_date,
        WorkoutSession.status == 'completed'
    ).group_by(
        'day_of_week'
    ).all()
    
    # Initialize counts for all days (0=Sunday, 6=Saturday)
    day_data = [0, 0, 0, 0, 0, 0, 0]
    
    # Fill in actual counts
    for day in day_counts:
        day_index = int(day.day_of_week)
        day_data[day_index] = day.count
    
    # Reorder to Monday first if needed
    # day_data = day_data[1:] + [day_data[0]]
    
    return {'data': day_data}

def prepare_top_exercises_chart(start_date, end_date):
    """Prepare data for top exercises by volume"""
    # Query for exercises and their volume
    exercise_volumes = db.session.query(
        Exercise.name,
        func.sum(ExerciseSet.weight * ExerciseSet.reps).label('volume')
    ).join(
        WorkoutEntry, 
        Exercise.id == WorkoutEntry.exercise_id
    ).join(
        ExerciseSet, 
        WorkoutEntry.id == ExerciseSet.workout_entry_id
    ).join(
        WorkoutSession, 
        WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutSession.date >= start_date,
        WorkoutSession.date <= end_date,
        WorkoutSession.status == 'completed'
    ).group_by(
        Exercise.name
    ).order_by(
        desc('volume')
    ).limit(10).all()
    
    labels = [e.name for e in exercise_volumes]
    data = [int(e.volume) for e in exercise_volumes]
    
    return {'labels': labels, 'data': data}

def prepare_exercise_progress_chart(exercise_id):
    """Prepare chart data for an exercise's progress over time"""
    # Get workout dates and max weight/volume for an exercise
    exercise_progress = db.session.query(
        WorkoutSession.date,
        func.max(ExerciseSet.weight).label('max_weight'),
        func.sum(ExerciseSet.weight * ExerciseSet.reps).label('volume')
    ).join(
        WorkoutEntry, 
        WorkoutSession.id == WorkoutEntry.session_id
    ).join(
        ExerciseSet, 
        WorkoutEntry.id == ExerciseSet.workout_entry_id
    ).filter(
        WorkoutEntry.exercise_id == exercise_id,
        WorkoutSession.status == 'completed'
    ).group_by(
        WorkoutSession.date
    ).order_by(
        WorkoutSession.date
    ).limit(10).all()
    
    labels = [p.date.strftime('%b %d') for p in exercise_progress]
    max_weight_data = [float(p.max_weight) for p in exercise_progress]
    volume_data = [int(p.volume) for p in exercise_progress]
    
    return {
        'labels': labels,
        'max_weight': max_weight_data,
        'volume': volume_data
    }

def prepare_muscle_volume_chart(muscle_name):
    """Prepare chart data for a muscle's volume over time"""
    # Get workout dates and volume for a muscle
    # Get last 10 dates when this muscle was worked
    muscle_dates = db.session.query(
        WorkoutSession.date,
        func.sum(ExerciseSet.weight * ExerciseSet.reps).label('volume')
    ).join(
        WorkoutEntry, 
        WorkoutSession.id == WorkoutEntry.session_id
    ).join(
        Exercise, 
        WorkoutEntry.exercise_id == Exercise.id
    ).join(
        exercise_muscle_association, 
        Exercise.id == exercise_muscle_association.c.exercise_id
    ).join(
        PrimaryMuscle, 
        exercise_muscle_association.c.muscle_id == PrimaryMuscle.id
    ).join(
        ExerciseSet, 
        WorkoutEntry.id == ExerciseSet.workout_entry_id
    ).filter(
        PrimaryMuscle.muscle == muscle_name,
        WorkoutSession.status == 'completed'
    ).group_by(
        WorkoutSession.date
    ).order_by(
        WorkoutSession.date
    ).limit(10).all()
    
    labels = [d.date.strftime('%b %d') for d in muscle_dates]
    values = [int(d.volume) for d in muscle_dates]
    
    return {'labels': labels, 'values': values}

def get_all_exercises_with_stats():
    """Get all exercises with their usage statistics"""
    exercises = Exercise.query.order_by(Exercise.name).all()
    
    for exercise in exercises:
        # Get the most recent usage and stats
        latest_entry = WorkoutEntry.query.filter_by(
            exercise_id=exercise.id
        ).join(
            WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
        ).filter(
            WorkoutSession.status == 'completed'
        ).order_by(
            WorkoutSession.date.desc()
        ).first()
        
        if latest_entry:
            # Calculate stats
            sets = ExerciseSet.query.join(
                WorkoutEntry, ExerciseSet.workout_entry_id == WorkoutEntry.id
            ).filter(
                WorkoutEntry.exercise_id == exercise.id
            ).all()
            
            exercise.stats = {
                'last_used': latest_entry.session.date.strftime('%b %d, %Y'),
                'total_sets': len(sets),
                'max_weight': max([s.weight for s in sets]) if sets else 0
            }
        else:
            exercise.stats = None
    
    return exercises

def get_all_muscles_with_stats():
    """Get all muscles with their usage statistics"""
    muscles = PrimaryMuscle.query.order_by(PrimaryMuscle.muscle).all()
    
    for muscle in muscles:
        # Count exercises that use this muscle
        exercise_count = db.session.query(func.count(Exercise.id)).join(
            exercise_muscle_association,
            Exercise.id == exercise_muscle_association.c.exercise_id
        ).filter(
            exercise_muscle_association.c.muscle_id == muscle.id
        ).scalar()
        
        # Count total sets that worked this muscle
        total_sets = db.session.query(func.count(ExerciseSet.id)).join(
            WorkoutEntry, ExerciseSet.workout_entry_id == WorkoutEntry.id
        ).join(
            Exercise, WorkoutEntry.exercise_id == Exercise.id
        ).join(
            exercise_muscle_association,
            Exercise.id == exercise_muscle_association.c.exercise_id
        ).filter(
            exercise_muscle_association.c.muscle_id == muscle.id
        ).scalar()
        
        muscle.exercise_count = exercise_count or 0
        muscle.total_sets = total_sets or 0
    
    return muscles

@views.route('/create-exercise', methods = ["GET"])
@login_required
def create_exercise():
    return render_template('create_exercise.html', user=current_user)

@views.route('/exercises', methods = ["GET"])
def exercises():
    # Eager load muscles to avoid N+1 queries
    exercises = Exercise.query.options(
        joinedload(Exercise.primary_muscles)
    ).all()

    return render_template( 'exercises.html',exercises=exercises, user=current_user)

# For a single exercise
@views.route('/exercise/<int:id>')
def exercise_detail(id):
    exercise = Exercise.query.options(
        joinedload(Exercise.primary_muscles)
    ).get_or_404(id)
    
    return render_template('exercise_detail.html', exercise=exercise, user=current_user)

@views.route('/exercises/muscle/<muscle_name>')
def exercises_by_muscle(muscle_name):
    exercises = Exercise.query.join(
        Exercise.primary_muscles
    ).filter(
        PrimaryMuscle.muscle == muscle_name
    ).all()
    
    return render_template('exercises_by_muscle.html', 
                         exercises=exercises, 
                         muscle_name=muscle_name,
                         user=current_user)

@views.route('/exercises/grouped')
def exercises_grouped():
    exercises = Exercise.query.options(
        joinedload(Exercise.primary_muscles)
    ).all()
    
    # Group by equipment
    grouped = defaultdict(list)
    for exercise in exercises:
        equipment = exercise.equipment or 'Bodyweight'
        grouped[equipment].append(exercise)
    
    return render_template('exercises_grouped.html', grouped_exercises=dict(grouped), user=current_user)

@views.route('/workout')
@login_required
def workout():
    # Get current workout session if exists
    workout_id = session.get('current_workout_id')
    workout_session = None
    
    if workout_id:
        workout_session = WorkoutSession.query.get(workout_id)
        # If completed or doesn't exist, clear session
        if not workout_session or workout_session.status == 'completed':
            session.pop('current_workout_id', None)
            workout_session = None
    
    # Get all muscles for filters
    all_primary_muscles = PrimaryMuscle.query.order_by(PrimaryMuscle.muscle).all()
    all_secondary_muscles = SecondaryMuscle.query.order_by(SecondaryMuscle.muscle).all()
    
    # Get selected filters
    selected_primary_muscles = request.args.getlist('primary_muscle')
    selected_secondary_muscles = request.args.getlist('secondary_muscle')
    
    # Filter exercises
    query = Exercise.query
    
    if selected_primary_muscles:
        query = query.join(Exercise.primary_muscles).filter(
            PrimaryMuscle.id.in_(selected_primary_muscles)
        )
    
    if selected_secondary_muscles:
        query = query.join(Exercise.secondary_muscles).filter(
            SecondaryMuscle.id.in_(selected_secondary_muscles)
        )
    
    filtered_exercises = query.options(
        joinedload(Exercise.primary_muscles),
        joinedload(Exercise.secondary_muscles)
    ).distinct().order_by(Exercise.name).all()
    
    # Get current exercise and sets
    current_exercise_id = session.get('current_exercise_id')
    current_exercise = None
    current_exercise_sets = []
    last_set = None
    all_workout_sets = []
    
    if workout_session and current_exercise_id:
        current_exercise = Exercise.query.options(
            joinedload(Exercise.primary_muscles),
            joinedload(Exercise.secondary_muscles)
        ).get(current_exercise_id)
        
        # Get sets for current exercise
        current_entry = WorkoutEntry.query.filter_by(
            session_id=workout_session.id,
            exercise_id=current_exercise_id
        ).first()
        
        if current_entry:
            current_exercise_sets = ExerciseSet.query.filter_by(
                workout_entry_id=current_entry.id
            ).order_by(ExerciseSet.set_number).all()
            
            if current_exercise_sets:
                last_set = current_exercise_sets[-1]
    
    # Get all workout entries if workout exists
    if workout_session:
        all_workout_sets = WorkoutEntry.query.filter_by(
            session_id=workout_session.id
        ).options(
            joinedload(WorkoutEntry.exercise),
            joinedload(WorkoutEntry.sets)
        ).all()
    
    return render_template('workout.html',
        workout_session=workout_session,
        all_primary_muscles=all_primary_muscles,
        all_secondary_muscles=all_secondary_muscles,
        selected_primary_muscles=selected_primary_muscles,
        selected_secondary_muscles=selected_secondary_muscles,
        filtered_exercises=filtered_exercises,
        current_exercise=current_exercise,
        current_exercise_sets=current_exercise_sets,
        last_set=last_set,
        all_workout_sets=all_workout_sets,
        user=current_user
    )

@views.route('/workout/start', methods=['POST'])
def start_workout():
    # Create new workout session
    workout_session = WorkoutSession(
        date=datetime.now(),
        workout_type='General',
        status='active',  # Add status field to your model
        user_id=current_user.id
    )
    db.session.add(workout_session)
    db.session.commit()
    
    session['current_workout_id'] = workout_session.id
    return jsonify({'success': True, 'workout_id': workout_session.id})

@views.route('/workout/pause', methods=['POST'])
def pause_workout():
    workout_id = session.get('current_workout_id')
    if workout_id:
        workout = WorkoutSession.query.get(workout_id)
        if workout:
            workout.status = 'paused'
            # Calculate and store elapsed time before pause
            elapsed = (datetime.now() - workout.date).total_seconds()
            workout.paused_at = datetime.now()
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False})

@views.route('/workout/resume', methods=['POST'])
def resume_workout():
    workout_id = session.get('current_workout_id')
    if workout_id:
        workout = WorkoutSession.query.get(workout_id)
        if workout and workout.status == 'paused':
            workout.status = 'active'
            # Calculate pause duration and add to total paused time
            if workout.paused_at:
                pause_duration = (datetime.now() - workout.paused_at).total_seconds()
                workout.paused_duration = (workout.paused_duration or 0) + pause_duration
            workout.paused_at = None
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False})

@views.route('/workout/restart', methods=['POST'])
def restart_workout():
    workout_id = session.get('current_workout_id')
    if workout_id:
        # Delete current workout and all associated data
        workout = WorkoutSession.query.get(workout_id)
        if workout:
            db.session.delete(workout)
            db.session.commit()
        
        # Create new workout
        new_workout = WorkoutSession(
            date=datetime.now(),
            workout_type='General',
            status='active',
            user=current_user.id
        )
        db.session.add(new_workout)
        db.session.commit()
        
        session['current_workout_id'] = new_workout.id
        session.pop('current_exercise_id', None)
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@views.route('/workout/finish', methods=['POST'])
def finish_workout():
    workout_id = session.get('current_workout_id')

    if workout_id:
        workout = WorkoutSession.query.get(workout_id)

        if workout:
            workout.status = 'completed'
            # Calculate total duration
            total_time = (datetime.now() - workout.date).total_seconds()
            if workout.paused_duration:
                total_time -= workout.paused_duration
            workout.duration_minutes = int(total_time / 60)
            db.session.commit()
            
            # Clear session
            session.pop('current_workout_id', None)
            session.pop('current_exercise_id', None)
            
            return jsonify({'success': True, 'workout_id': workout.id})
    
    return jsonify({'success': False})

@views.route('/select_exercise', methods=['POST'])
def select_exercise():
    exercise_id = request.form.get('exercise_id')
    session['current_exercise_id'] = int(exercise_id) if exercise_id else None
    return redirect(url_for('views.workout'))

@views.route('/add_set', methods=['POST'])
def add_set():
    workout_id = request.form.get('workout_id')
    exercise_id = request.form.get('exercise_id')
    weight = float(request.form.get('weight'))
    reps = int(request.form.get('reps'))
    
    # Get or create workout entry
    entry = WorkoutEntry.query.filter_by(
        session_id=workout_id,
        exercise_id=exercise_id
    ).first()
    
    if not entry:
        entry = WorkoutEntry(
            session_id=workout_id,
            exercise_id=exercise_id,
            order=1  # You might want to calculate this
        )
        db.session.add(entry)
        db.session.flush()
    
    # Get the next set number
    last_set = ExerciseSet.query.filter_by(
        workout_entry_id=entry.id
    ).order_by(ExerciseSet.set_number.desc()).first()
    
    set_number = (last_set.set_number + 1) if last_set else 1
    
    # Create new set
    new_set = ExerciseSet(
        workout_entry_id=entry.id,
        set_number=set_number,
        weight=weight,
        reps=reps,
        timestamp=datetime.now()
    )
    
    db.session.add(new_set)
    db.session.commit()
    
    return redirect(url_for('views.workout'))

@views.route('/delete_set/<int:set_id>', methods=['POST'])
def delete_set(set_id):
    exercise_set = ExerciseSet.query.get_or_404(set_id)
    db.session.delete(exercise_set)
    db.session.commit()
    return redirect(url_for('views.workout'))

@views.route('/workout/summary/<int:workout_id>')
@login_required
def workout_summary(workout_id):
    # Get the completed workout
    workout = WorkoutSession.query.get_or_404(workout_id)
    
    # Get all entries for this workout with relationships
    workout_entries = WorkoutEntry.query.filter_by(
        session_id=workout_id
    ).options(
        joinedload(WorkoutEntry.exercise).joinedload(Exercise.primary_muscles),
        joinedload(WorkoutEntry.exercise).joinedload(Exercise.secondary_muscles),
        joinedload(WorkoutEntry.sets)
    ).all()
    
    # Calculate statistics for each entry
    for entry in workout_entries:
        entry.stats = {
            'sets': len(entry.sets),
            'reps': sum(s.reps for s in entry.sets),
            'volume': sum(s.weight * s.reps for s in entry.sets),
            'max_weight': max(s.weight for s in entry.sets) if entry.sets else 0,
            'avg_reps': sum(s.reps for s in entry.sets) / len(entry.sets) if entry.sets else 0
        }
    
    # Calculate total workout statistics
    total_stats = {
        'exercises': len(workout_entries),
        'sets': sum(len(entry.sets) for entry in workout_entries),
        'reps': sum(sum(s.reps for s in entry.sets) for entry in workout_entries),
        'volume_lbs': sum(sum(s.weight * s.reps for s in entry.sets) for entry in workout_entries)
    }
    
    return render_template('workout_summary.html', 
                          workout=workout,
                          workout_entries=workout_entries,
                          total_stats=total_stats,
                          user=current_user)

@views.route('/workout/download/<int:workout_id>')
@login_required
def download_workout(workout_id):
    # This is a placeholder for a download feature
    # You could generate a PDF or CSV here
    # For now, just redirect back to the summary
    return redirect(url_for('views.workout_summary', workout_id=workout_id), user=current_user)
