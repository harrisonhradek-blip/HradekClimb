# HradekClimb
#### VIDEO DEMO: https://youtu.be/Ukna5O76W1Y
#### Description:

A Small website designed to help anyone who uses it track their climbs, helping them improve and see their progress over a long period of time.

## Install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Use:

```bash
# Run a local server on your device to start the local website
flask run
```

The website should be hosted on `http://127.0.0.1:5000/` now, you can go to your web browser and now go to the port

You can log in with:

username: test
password: test

for sample datasets

## How login and register work:

Each and every password is stored via hashing using the `werkzeug.security` library upon loggin in via register. After the user enters a login and password via the `/register` route, the data is stored in the `users` database seen in `climbing.db`. After the username and password is stored on the database, the user is redirected the the `/login` page.

To actually access the home page, the user must not type in their now stored username and password; if any user errors occur, banners pop up displaying what the user did wrong instead of a redirect to an error page, which I thought was much nicer looking and a better UX experience.

Once the user submits a valid username and password, `/login` retrieves the data from the `users` database and compares the hashed version of the password the user is trying to log into, and the password stored on the database. If the hashed passwords match, the user is logged in and redirected the `/index` page.

## How the homepage displays data:

The homepage is split up into 3 different sections; The top left displays the users best grades of each month of the sessions that they logged; On the top right is a graph from `chart.js` that displays a line graph of the users climbing volume, month after month, which can be used to measure consistency. At the bottom of the page is a list of every session the user logged. In each row is the index of the climb (randomly generated), the date the climb was added, how many climbs the user did, and what the highest grade was out of all the climbs the did. Additionally there are 2 buttons, `edit`, and `delete`. Later you'll understand more about what they do, but essentially they allow the user to update and change what they have already logged, or delete the session entirely from the database.

## How a session is stored:

Once the user gets bored of looking at a blank homepage, they will probably want to add some data... When they click the `log session` button in the header of the page, they will be redirected to the `/log` route, very similar to the homepage except there is an option to add a session, allowing them to enter in the amount of climbs they did in the session they want to log. Once this #of climbs is submitted, the user is redirected to `/log_session` Where a number of empty climb sets are automatically generated. Underneath `New Session`, each climb has 4 points of data to enter in: 1. the amount of hours spent on a given climb, 2. the grade of which the climb is, 3. whether they completed it or "sent" it, and 4. the number of attempts the user spent completing (or trying to complete) the climb.

## How the database stores data:

`climbing.db` is split into 4 tables:

- users: This, as explained before stores a hash of all the passwords as well as a username, and a unique id for each user to be referenced to.
- user_sessions: Stores a session id for each new session logged, the user_id associated with it, and the date that it was logged
- session_climbs: Stores a climb id for each climb, the session_id the climb is associated with, and the number of hours the user claimed they spent on it.
- climb_data: Where most of the data is stored; contains the climb id referenced above, the grade the climb is as a string, the grade as a integer, whether they completed it (stored as 0 or 1) and the amount of attempts. You curiously also might see a difficulty column with "null" as every value, this was created if I wanted to add a option to give your own personal rating, but I decided it would not be that important for tracking you're progress compared to the others.

`climb_data <- session_climbs <- user_sessions <- users `

## How data is deleted:

Whenever the user clicks delete on any of the sessions `app.py` in the `/index` route is treated as a post method, this will just go one by one on each level of the data base deleting each one, starting with the climb data, then the session data, and then any reference to the data.

## How HradekClimb is different (and similar) to finance:

#### Different:

- While the finance.db schema is essentially broken into 2 tables, climbing.db is more complex as it used 4, with normalized referencing, meaningfully storing and handeling more data

- /log_session flow generates a variable number of climb-entry rows based on user input, then parses them back with request.form.getlist(...) and puts them all together in the same list.

- Computes hardest grade overall and per month (strftime grouping), send rate, average attempts per grade, monthly volume, then feeds one of those into a Chart.js line graph. Finance has no charting or time-series grouping at all.

- Finance has no edit/update feature for past transactions.

#### Similar:

- Auth login and register is directly adapted from finance.

- Single user dashboard behind login, backed by SQLite via the cs50 library, server-rendered with Flask/Jinja, POST-redirect-GET pattern throughout. Structurally similar to Finance at a high level.

## File Overview

- **`app.py`**: the Flask application. Defines every route: `/` (the
  dashboard, and the POST target for deleting a session), `/login`,
  `/register`, `/logout`, `/log` (choose how many climbs to log), `/log_session`
  (submit the generated climb form), and `/edit` (update an existing
  session). This is where all the SQL queries are, wher computing hardest
  grade, monthly stats, send rate, and volume, and reading/writing the
  four database tables happens aswell.

- **`helpers.py`**: holds the `login_required` decorator, adapted from
  Finance, which wraps any route that should redirect to `/login` if
  there's no active session.

- **`climbing.db`**: the SQLite database, with four tables: `users`,
  `user_sessions`, `session_climbs`, and `climb_data`. See the "How the
  database stores data" section above for the schema.

- **`seed_data.py`**: an optional script that populates `climbing.db`
  with sample sessions for the `test` user, so the dashboard has data to
  show instead of starting empty. Safe to re-run.

- **`requirements.txt`**: the Python packages needed to run the app
  (`cs50`, `Flask`, `Flask-Session`).

- **`templates/layout.html`**: the shared page shell every other
  template extends: navbar (which changes based on whether you're
  logged in), flashed-message banners, and the Bootstrap/Chart.js CDN
  links.

- **`templates/index.html`**: the dashboard: monthly-highest-grade
  list, average-attempts-per-grade list, the Chart.js volume line
  graph, and the session table with its Edit/Delete buttons.

- **`templates/log.html`**: shown when you click "Log session"; lets
  you pick how many climbs you're about to log before generating the
  form for them.

- **`templates/log_session.html`**: the generated form itself, with
  one row of inputs (hours, grade, sent, attempts) per climb.

- **`templates/edit.html`**: lets you update the climbs in an existing
  session.

- **`templates/login.html`** / **`templates/register.html`** — standard
  login and registration forms.

- **`static/styles.css`**: custom styling on top of Bootstrap.

- **`static/climbing.jpg`** / **`static/climbing.ico`**: background
  image and favicon.

## Notes:

 - 961 words (didn't count overview or sample data)
 - Sample data done by ai (claude)

 ## Sample Data (optional):

If you'd like to see the dashboard populated with data instead of starting
from a blank homepage, a seed script is included.

```bash
python3 seed_data.py
```

This creates a user with username `test` and password `test`, then inserts
6 months of sample climbing sessions so the charts and monthly-bests list
have something to show. Log in with:

- **Username:** `test`
- **Password:** `test`

The script is safe to re-run — if the `test` user already exists it reuses
it instead of creating a duplicate. 