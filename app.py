from flask import Flask, render_template, request, redirect, url_for, flash, session
from collections import deque
from functools import wraps
import database

from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Admin account
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not app.secret_key or not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise RuntimeError("Missing environment settings. Check your .env file.")

# Initialize SQLite database
database.initialize_database()

# Load saved students into a Python List
students = database.load_students()

# Registration Queue using deque
registration_queue = deque(database.load_queue())


# Login protection
def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if "login_attempts" not in session:
        session["login_attempts"] = 0

    if session["login_attempts"] >= 3:
        flash("Too many failed attempts. Please restart your session.")
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = username
            session.pop("login_attempts", None)
            flash("Welcome, Admin!")
            return redirect(url_for("home"))

        session["login_attempts"] += 1
        flash("Incorrect username or password.")

    return render_template("login.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have successfully logged out.")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    search = request.args.get("search", "").strip().lower()

    filtered_students = [
        s for s in students
        if search in s["student_id"].lower()
        or search in s["full_name"].lower()
        or search in s["course"].lower()
    ]

    return render_template(
        "index.html",
        students=filtered_students,
        search=search
    )


@app.route("/add_student", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        student_id = request.form["student_id"].strip()
        full_name = request.form["full_name"].strip()
        course = request.form["course"].strip()
        year_level = request.form["year_level"].strip()

        if not student_id.isdigit():
            flash("Student ID must contain numbers only.")
            return redirect(url_for("add_student"))

        if any(s["student_id"] == student_id for s in students):
            flash("Student ID already exists.")
            return redirect(url_for("add_student"))

        if not full_name or not course:
            flash("All fields are required.")
            return redirect(url_for("add_student"))

        if not year_level.isdigit() or not 1 <= int(year_level) <= 6:
            flash("Year level must be between 1 and 6.")
            return redirect(url_for("add_student"))

        new_student = {
            "student_id": student_id,
            "full_name": full_name,
            "course": course,
            "year_level": year_level
        }

        database.add_student(new_student)
        students.append(new_student)

        flash("Student successfully added!")
        return redirect(url_for("home"))

    return render_template("add_student.html")


@app.route("/edit_student/<student_id>", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    student = next(
        (s for s in students if s["student_id"] == student_id),
        None
    )

    if student is None:
        flash("Student not found.")
        return redirect(url_for("home"))

    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        course = request.form["course"].strip()
        year_level = request.form["year_level"].strip()

        if not full_name or not course:
            flash("All fields are required.")
            return redirect(url_for("edit_student", student_id=student_id))

        if not year_level.isdigit() or not 1 <= int(year_level) <= 6:
            flash("Year level must be between 1 and 6.")
            return redirect(url_for("edit_student", student_id=student_id))

        student["full_name"] = full_name
        student["course"] = course
        student["year_level"] = year_level

        database.update_student(student)

        flash("Student record updated!")
        return redirect(url_for("home"))

    return render_template("edit_student.html", student=student)


@app.route("/delete_student/<student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    global registration_queue

    database.delete_student(student_id)

    students[:] = [
        s for s in students if s["student_id"] != student_id
    ]

    registration_queue = deque(
        q for q in registration_queue
        if q["student_id"] != student_id
    )

    database.delete_from_queue(student_id)

    flash("Student record deleted.")
    return redirect(url_for("home"))


@app.route("/queue", methods=["GET", "POST"])
@login_required
def queue():
    if request.method == "POST":
        student_id = request.form["student_id"].strip()

        student = next(
            (s for s in students if s["student_id"] == student_id),
            None
        )

        if student is None:
            flash("Student ID not found.")

        elif any(q["student_id"] == student_id for q in registration_queue):
            flash("Student is already in the queue.")

        else:
            registration_queue.append(student.copy())
            database.add_to_queue(student)

            flash("Student added to registration queue.")

        return redirect(url_for("queue"))

    return render_template(
        "queue.html",
        registration_queue=list(registration_queue),
        students=students
    )


@app.route("/process_queue", methods=["POST"])
@login_required
def process_queue():
    if registration_queue:
        processed = registration_queue.popleft()
        database.remove_from_queue()

        flash(f"Processed registration for {processed['full_name']}.")
    else:
        flash("The registration queue is empty.")

    return redirect(url_for("queue"))

if __name__ == "__main__":
    app.run(debug=False)