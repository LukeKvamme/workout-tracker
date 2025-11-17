# Workout-Tracker App

---

## Architecture Diagram
<img width="721" height="782" alt="Image" src="https://github.com/user-attachments/assets/08d547c7-b762-4275-8a02-7833bbb739fb" />

---

## During Exercise
The app it designed to be used while working out. After each set, you can log a new set through the /log-set path.
This stores the data within the MariaDB container.

If there is an exercise that does not yet exist in the database and thus not visible within the log-set page, there is a
/create-new-exercise path where I can create a new exercise with a:
1. Name
2. Muscle Group
3. Equipment used for the lift
4. Optional - Notes about the exercise

On mobile, this is what the pages look like:
Log Set:
![Image](https://github.com/user-attachments/assets/4e7d4261-489d-4815-a899-712635d03fbb)
Create New Exercise:
![Image](https://github.com/user-attachments/assets/6925389f-b702-40f4-ae75-88a7a284f01b)

---

## Under Development
There are currently two unused pages:
1. / (home page)
2. /analytics

The next steps are to create Grafana dashboards that are linked inside the /analytics page for viewing analytics within the app itself.
Still unsure about what to display in the home page, but I am thinking to have the historical lift stats here (more granular in /analytics).

Current Grafana dashboard for viewing historical workout data (idea is to split into muscle groups and link within analytics page):
<img width="800" height="865" alt="Image" src="https://github.com/user-attachments/assets/42af7e40-dc51-4765-916f-ebfc8f183134" />

Also under development:
- A way to refresh the database connection (easy to do with Javascript, but idea with Dash is to not need js) for create exercise > log set
- Displaying previous sets on /log-set page (not just the text after logging a new set, but a proper Div containing the stats of previous sets in current workout)
- Maybe functionality to have multiple users (gf does not seem to care about logging her workouts in an app that is not Apple Notes)
