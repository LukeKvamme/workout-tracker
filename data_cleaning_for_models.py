import os
import json


def make_list():
    '''
    One-time use script to create the initial load file for each exercises, taken from a very large dataset from github.
    Aggregates into a large JSON file for upload into sqlite database initialization for the Exercise model.
    '''
    exercise_dir = "exercises"
    exercise_dir_list = os.listdir(exercise_dir)

    running_total_exercises = []
    for exercise in exercise_dir_list:
        exercise_subdir = os.path.join(exercise_dir, exercise)
        with open(os.path.join(exercise_subdir, "exercise.json"), 'r') as f:
            new_exercise_data = json.load(f)
            running_total_exercises.append(new_exercise_data)


    with open("output\exercises.json", 'w') as j:
        json.dump(running_total_exercises, j, indent=4)

def get_all_primary_muscles():
    '''
    One-time use script to get unique primary muscles, this will be used to initialize the PrimaryMuscle table.
    '''
    exercise_dir = "exercises"
    exercise_dir_list = os.listdir(exercise_dir)

    running_total_muscles = []
    for exercise in exercise_dir_list:
        exercise_subdir = os.path.join(exercise_dir, exercise)
        with open(os.path.join(exercise_subdir, "exercise.json"), 'r') as f:
            new_exercise_data = json.load(f)
            primary_muscles = new_exercise_data['primaryMuscles']
            for muscle in primary_muscles:
                running_total_muscles.append(muscle)

    unique_total_muscles = sorted(list(set(running_total_muscles)))

    with open("output\primary_muscles.json", 'w') as j:
        json.dump(unique_total_muscles, j, indent=4)

def get_all_secondary_muscles():
    '''
    One-time use script to get unique secondary muscles, this will be used to initialize the SecondaryMuscle table.
    '''
    exercise_dir = "exercises"
    exercise_dir_list = os.listdir(exercise_dir)

    running_total_muscles = []
    for exercise in exercise_dir_list:
        exercise_subdir = os.path.join(exercise_dir, exercise)
        with open(os.path.join(exercise_subdir, "exercise.json"), 'r') as f:
            new_exercise_data = json.load(f)
            secondary_muscles = new_exercise_data['secondaryMuscles']
            for muscle in secondary_muscles:
                running_total_muscles.append(muscle)

    unique_total_muscles = sorted(list(set(running_total_muscles)))

    with open("output\secondary_muscles.json", 'w') as j:
        json.dump(unique_total_muscles, j, indent=4)



##########################################################################
if __name__ == '__main__':
    # make_list()
    '''separate scripts in case'''
    # get_all_primary_muscles()
    # get_all_secondary_muscles()