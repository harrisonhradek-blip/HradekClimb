import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app=app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///climbing.db")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Show dash board of the users climbs, and their average grade, and trends
    if request.method == "POST":
        db.execute("""
            DELETE FROM climb_data
            WHERE climb_id IN (
                SELECT sc.climb_id FROM session_climbs sc
                JOIN user_sessions us ON sc.session_id = us.session_id
                WHERE sc.session_id = ? AND us.user_id = ?
            )
        """, request.form.get("session_id"), session["user_id"])

        db.execute("""
            DELETE FROM session_climbs
            WHERE session_id = ? AND session_id IN (
                SELECT session_id FROM user_sessions WHERE user_id = ?
            )
        """, request.form.get("session_id"), session["user_id"])

        db.execute("""
            DELETE FROM user_sessions
            WHERE session_id = ? AND user_id = ?
        """, request.form.get("session_id"), session["user_id"])
        return redirect("/") # This was here so if in the future i wanted to add a feature regarding the homepage
    else:

        # Get data of all climbs from every session where the id is the user's id
        
        # Calc Hardest Grade
        row = db.execute("""
            SELECT MAX(cd.grade_numeric) AS hardest
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ? AND cd.sent = 1
        """, session["user_id"])

        highest = row[0]["hardest"]  # None if no sends yet, otherwise an int

        # Calc Hardest Grade Per month
        monthly_highest = db.execute("""
            SELECT strftime('%Y-%m', us.date) AS month, MAX(cd.grade_numeric) AS hardest
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ? AND cd.sent = 1
            GROUP BY month
            ORDER BY month
        """, session["user_id"])

        #Calc Send Rate
        row = db.execute("""
            SELECT SUM(CASE WHEN cd.sent = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS send_rate
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ?
        """, session["user_id"])

        send_rate = row[0]["send_rate"] if row[0]["send_rate"] is not None else 0

        # Calc avg attempts per send
        avg_attempts = db.execute("""
            SELECT cd.grade_numeric AS grade, AVG(cd.attempts) AS avg_attempts
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ? AND cd.sent = 1
            GROUP BY cd.grade_numeric
            ORDER BY cd.grade_numeric
        """, session["user_id"])

        # Calc volume trend

        # Populate dict 
        sessions = db.execute("""
            SELECT us.session_id, us.date,
                MAX(CASE WHEN cd.sent = 1 THEN cd.grade_numeric END) AS highest_sent,
                COUNT(cd.climb_id) AS climb_count
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ?
            GROUP BY us.session_id
            ORDER BY us.date DESC
        """, session["user_id"])

        volume = db.execute("""
            SELECT strftime('%Y-%m', us.date) AS month, COUNT(cd.climb_id) AS climb_count
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ?
            GROUP BY month
            ORDER BY month
        """, session["user_id"])

        row = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])
        name = row[0]["username"]

        return render_template("index.html",
                               highest=highest,
                               monthly_highest=monthly_highest,
                               send_rate=send_rate,
                               avg_attempts=avg_attempts,
                               sessions=sessions,
                               volume=volume,
                               name=name
                               )  

@app.route("/login", methods=["GET", "POST"])
def login(): # snippet from finance
    """Log user in"""

    # Forget any user_id
    session.pop("user_id", None)
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Please use a valid username.", "danger")
            return redirect("/login")
        
        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Please enter a password.", "danger")
            return redirect("/login")  

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("Password or Username is Incorrect.", "danger")
            return redirect("/login")  

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register(): # register the user into the database (similar to finance)
    """Register user"""
    session.pop("user_id", None)

    if request.method == "POST":
        if not request.form.get("username"):
            flash("Please use a valid username.", "danger")
            return redirect("/register")
        
        elif not request.form.get("password"):
            flash("Please enter a password.", "danger")
            return redirect("/register")        
        
        if request.form.get("password") != request.form.get("confirmation"):
            flash("Passwords do not match.", "danger")
            return redirect("/register")         
        
        username = request.form.get("username")
        hash = generate_password_hash(request.form.get("password"))
        
        try:
            db.execute(
                "INSERT INTO users (username, hash) VALUES(?, ?)", username, hash
            )
            return redirect("/")
        except ValueError:
            flash("Something went Wrong.", "danger")
            return redirect("/login")          
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():

    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/log", methods=["GET", "POST"])
def log(): # just collects how many climbs the user wants to do for ease of rendering the template
    if request.method == "POST":
        climbs = request.form.get("climbs")
        if not climbs or not climbs.isdigit():
            flash("Please enter a valid number of climbs.", "danger")
            return redirect("/log")
        return render_template("log_session.html", climbs=int(climbs))
    else:
    # NOTE: Claude helped me create some of these queries that involve strftime, although the underlying logic is still mine

        # Get data of all climbs from every session where the id is the user's id
        
        # Calc Hardest Grade
        row = db.execute("""
            SELECT MAX(cd.grade_numeric) AS hardest
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ? AND cd.sent = 1
        """, session["user_id"])

        highest = row[0]["hardest"]  # None if no sends yet, otherwise an int

        # Calc Hardest Grade Per month
        monthly_highest = db.execute("""
            SELECT strftime('%Y-%m', us.date) AS month, MAX(cd.grade_numeric) AS hardest
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ? AND cd.sent = 1
            GROUP BY month
            ORDER BY month
        """, session["user_id"])

        #Calc Send Rate
        row = db.execute("""
            SELECT SUM(CASE WHEN cd.sent = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS send_rate
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ?
        """, session["user_id"])

        send_rate = row[0]["send_rate"] if row[0]["send_rate"] is not None else 0

        # Calc avg attempts per send
        avg_attempts = db.execute("""
            SELECT cd.grade_numeric AS grade, AVG(cd.attempts) AS avg_attempts
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ? AND cd.sent = 1
            GROUP BY cd.grade_numeric
            ORDER BY cd.grade_numeric
        """, session["user_id"])


        # Populate dict 
        sessions = db.execute("""
            SELECT us.session_id, us.date,
                MAX(CASE WHEN cd.sent = 1 THEN cd.grade_numeric END) AS highest_sent,
                COUNT(cd.climb_id) AS climb_count
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ?
            GROUP BY us.session_id
            ORDER BY us.date DESC
        """, session["user_id"])
        # find the volume for each month
        volume = db.execute("""
            SELECT strftime('%Y-%m', us.date) AS month, COUNT(cd.climb_id) AS climb_count
            FROM climb_data cd
            JOIN session_climbs sc ON cd.climb_id = sc.climb_id
            JOIN user_sessions us ON sc.session_id = us.session_id
            WHERE us.user_id = ?
            GROUP BY month
            ORDER BY month
        """, session["user_id"])

        return render_template("log.html",
                               highest=highest,
                               monthly_highest=monthly_highest,
                               send_rate=send_rate,
                               avg_attempts=avg_attempts,
                               sessions=sessions,
                               volume=volume
                               )  

@app.route("/log_session", methods=["GET", "POST"])
def log_session():
    if request.method == "POST":
        try:
            #check for dummy select
            for i in request.form.getlist("send[]"):
                if i == "Select":
                    flash("Please select a ""send"".", "danger")
                    return redirect("/log_session")   
            for i in request.form.getlist("grade[]"):
                if i == "grade":
                    flash("Please select a ""grade"".", "danger")
                    return redirect("/log_session")   

            # Create climb data
            climb_data = []
            # get arrays of all the inputs the user sent
            hours = request.form.getlist("hours[]")
            grade = request.form.getlist("grade[]")
            grade_numeric = [int(i[1:]) for i in grade] # simply gets rid of the "v" at the begining of each one   
            sent = [1 if s == "yes" else 0 for s in request.form.getlist("sent[]")] # turns "yes" or "no" into 1 and 0
            attempts = request.form.getlist("attempts[]")

            climbs = int(request.form.get("climbs"))
            for climb in range(climbs):
                climb_data.append({
                    "climb" : climb, # just for redundancy giving each row the corresponding climb
                    "hours" : hours[climb],
                    "grade" : grade[climb],
                    "grade_numeric" : grade_numeric[climb],
                    "sent" : sent[climb],
                    "attempts" : attempts[climb]
                })

            # creates a new session that will create a unique id for the climbs to be inserted into
            session_id = db.execute(
                "INSERT INTO user_sessions (user_id) VALUES(?)",
                session["user_id"]
            )
            # puts the climbs into the session along with how many hours they spent
            for climb in climb_data:
                new_climb_id = db.execute("""
                    INSERT INTO session_climbs (session_id, hours) VALUES(?, ?)
                """, session_id, climb["hours"])

                db.execute("""
                    INSERT INTO climb_data (climb_id, grade, grade_numeric, sent, attempts) VALUES(?, ?, ?, ?, ?)
                """, new_climb_id, climb["grade"], climb["grade_numeric"], climb["sent"], climb["attempts"])

            # go back to homepage
            return redirect("/")
        except ValueError:
            flash("Fill out all the information.", "danger")
            return redirect("/")
    else:
        return redirect("/")

@app.route("/edit", methods=["GET", "POST"])
def edit():

    if request.method == "POST":

        session_id = request.form.get("session_id")
        climb_data = []

        # get arrays of all the inputs the user sent
        climb_ids = request.form.getlist("climb_id[]")
        hours = request.form.getlist("hours[]")
        grade = request.form.getlist("grade[]")
        grade_numeric = [int(i[1:]) for i in grade] # simply gets rid of the "v" at the begining of each one   
        sent = [1 if s == "yes" else 0 for s in request.form.getlist("sent[]")] # turns "yes" or "no" into 1 and 0
        attempts = request.form.getlist("attempts[]")

        for i in range(len(climb_ids)):
            climb_data.append({
                "climb_id": climb_ids[i],
                "hours": hours[i],
                "grade": grade[i],
                "grade_numeric": grade_numeric[i],
                "sent": sent[i],
                "attempts": attempts[i]
            })

        # puts the climbs into the session along with how many hours they spent

        for climb in climb_data:
            # insert into session_climbs
            db.execute("""
                UPDATE session_climbs SET hours = ?
                WHERE climb_id = ? AND session_id = ?
            """, climb["hours"], climb["climb_id"], session_id)

            # now use that generated ID for the matching climb_data row
            db.execute("""
                UPDATE climb_data
                SET grade = ?, grade_numeric = ?, sent = ?, attempts = ?
                WHERE climb_id = ?
            """, climb["grade"], climb["grade_numeric"], climb["sent"], climb["attempts"], climb["climb_id"])

        return redirect("/") 
    else:    

        session_id = request.args.get("session_id")

        climbs = db.execute("""
            SELECT climb_data.*, session_climbs.hours FROM climb_data
            JOIN session_climbs ON climb_data.climb_id = session_climbs.climb_id
            JOIN user_sessions ON session_climbs.session_id = user_sessions.session_id
            WHERE session_climbs.session_id = ? AND user_sessions.user_id = ?
        """, session_id, session["user_id"])

        hours = db.execute("""
            SELECT session_climbs.hours FROM session_climbs
            JOIN user_sessions ON session_climbs.session_id = user_sessions.session_id
            WHERE session_climbs.session_id = ? AND user_sessions.user_id = ?
        """, session_id, session["user_id"])

        return render_template("edit.html", climbs=climbs, session_id=session_id)
