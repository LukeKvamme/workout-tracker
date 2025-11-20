# Workout-Tracker App

---

## Architecture Diagram
<img width="721" height="821" alt="Image" src="https://github.com/user-attachments/assets/9400a2d1-6836-4fba-aef7-9c6234c3977c" />

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

## Analytics
Right now, has an embedded Grafana dashboard within an iFrame showing in the /analytics page that looks like this:
<img width="645" height="1310" alt="Image" src="https://github.com/user-attachments/assets/b75211ca-d5e2-46c7-8b6e-e45ca1fc1938" />

This just displays historical stats on lifts right now, but in the future the plan is to add a dashboard for each muscle group, then there will be a muscle group radial button to select and view through the different dashboards.

Each dashboard requires two different links due to different IP's to access Grafana on the server:
- Local view
- Tailscale view

---

## Under Development
There is currently one unused page:
1. / (home page)

Still unsure about what to display in the home page, but I am thinking to move the historical lift stats here (and then have the more granular views in /analytics).

---
## Also under development:
- Multiple grafana dashboards for more granular muscle_grouping view
- Something more substantial with the Home page
- Style the previous sets better than current display, maybe always display them as well (not just post-new log. think about closing and re-opening the app)
- Maybe functionality to have multiple users (gf does not seem to care about logging her workouts in an app that is not Apple Notes)
- RPE input (low priority, not sure if I even ever want to use this but added it to schema just in case)
- Depending on Dash.html.Video functionality, maybe hook up to local-tiktok...?
