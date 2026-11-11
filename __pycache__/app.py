import os
from datetime import timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import database
from database import init_db, get_db, test_mysql_connection
import analytics

app = Flask(__name__)
app.secret_key = "golden_rice_placement_secure_secret_key_2026"
app.permanent_session_lifetime = timedelta(days=30)

# Context processor to inject database status and current_user into every template
@app.context_processor
def inject_global_context():
    return dict(
        db_status=database.active_db_info,
        current_user=session.get("user")
    )

@app.before_request
def check_initialized():
    if not hasattr(app, '_db_initialized'):
        init_db()
        app._db_initialized = True

# Authentication Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to access the placement system.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# --- Authentication Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "")
        remember_me = request.form.get("remember_me")

        if not login_id or not password:
            flash("Username/email and password are required.", "danger")
            return redirect(url_for("login"))

        with get_db() as (conn, engine):
            cursor = conn.cursor()
            q = ("SELECT * FROM users WHERE username = %s OR email = %s" 
                 if engine == "mysql" else 
                 "SELECT * FROM users WHERE username = ? OR email = ?")
            cursor.execute(q, (login_id, login_id))
            user = cursor.fetchone()

        if user:
            user_dict = dict(user) if not isinstance(user, dict) else user
            stored_hash = user_dict.get("password_hash")
            
            if check_password_hash(stored_hash, password):
                # Valid credentials
                session_user = {
                    "user_id": user_dict.get("user_id"),
                    "username": user_dict.get("username"),
                    "email": user_dict.get("email"),
                    "role": user_dict.get("role", "Admin")
                }
                session["user"] = session_user

                next_page = request.args.get("next") or url_for("dashboard")
                resp = make_response(redirect(next_page))

                # Handle "Remember Me"
                if remember_me:
                    session.permanent = True
                    # Cookie saved for 30 days
                    resp.set_cookie("remembered_login_id", login_id, max_age=30*24*60*60, httponly=True)
                else:
                    session.permanent = False
                    resp.delete_cookie("remembered_login_id")

                flash(f"Welcome back, {session_user['username']}! Signed in successfully.", "success")
                return resp

        flash("Invalid username/email or password. Please try again.", "danger")
        return redirect(url_for("login"))

    remembered_login_id = request.cookies.get("remembered_login_id", "")
    return render_template("login.html", remembered_login_id=remembered_login_id)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "Placement Officer")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        remember_me = request.form.get("remember_me")

        # Validations
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("signup"))

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match. Please verify and re-enter.", "danger")
            return redirect(url_for("signup"))

        with get_db() as (conn, engine):
            cursor = conn.cursor()
            # Check unique username or email
            check_q = ("SELECT user_id FROM users WHERE username = %s OR email = %s"
                       if engine == "mysql" else
                       "SELECT user_id FROM users WHERE username = ? OR email = ?")
            cursor.execute(check_q, (username, email))
            existing = cursor.fetchone()
            if existing:
                flash("Username or email is already registered. Please sign in instead.", "warning")
                return redirect(url_for("login"))

            # Create user
            p_hash = generate_password_hash(password)
            insert_q = ("INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)"
                        if engine == "mysql" else
                        "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)")
            cursor.execute(insert_q, (username, email, p_hash, role))
            conn.commit()
            new_uid = cursor.lastrowid

        # Auto-login after registration
        session_user = {
            "user_id": new_uid,
            "username": username,
            "email": email,
            "role": role
        }
        session["user"] = session_user

        resp = make_response(redirect(url_for("dashboard")))
        if remember_me:
            session.permanent = True
            resp.set_cookie("remembered_login_id", username, max_age=30*24*60*60, httponly=True)

        flash(f"Account created successfully! Welcome to Project Golden Rice, {username}.", "success")
        return resp

    return render_template("signup.html")

@app.route("/logout")
def logout():
    username = session.get("user", {}).get("username", "User")
    session.pop("user", None)
    flash(f"Goodbye {username}! You have been logged out securely.", "info")
    return redirect(url_for("login"))

# --- Protected Application Routes ---
@app.route("/")
@login_required
def dashboard():
    kpis = analytics.calculate_kpis()
    dept_stats = analytics.get_department_analysis()
    skills = analytics.get_skill_demand()
    charts = analytics.generate_charts()
    return render_template("dashboard.html", kpis=kpis, dept_stats=dept_stats, skills=skills, charts=charts)

# --- Students CRUD ---
@app.route("/students", methods=["GET", "POST"])
@login_required
def students():
    if request.method == "POST":
        roll = request.form.get("roll_number", "").strip()
        name = request.form.get("full_name", "").strip()
        dept = request.form.get("department")
        year = request.form.get("graduation_year", type=int)
        cgpa = request.form.get("cgpa", type=float)
        backlogs = request.form.get("active_backlogs", type=int, default=0)

        if not roll or not name or not dept or not year or cgpa is None:
            flash("All student fields are required.", "danger")
            return redirect(url_for("students"))

        if not (0.0 <= cgpa <= 10.0):
            flash("CGPA must be between 0.0 and 10.0.", "warning")
            return redirect(url_for("students"))

        is_eligible = 1 if (cgpa >= 6.0 and backlogs == 0) else 0

        with get_db() as (conn, engine):
            cursor = conn.cursor()
            try:
                q = ("INSERT INTO students (roll_number, full_name, department, graduation_year, cgpa, active_backlogs, is_eligible) VALUES (%s, %s, %s, %s, %s, %s, %s)" 
                     if engine == "mysql" else 
                     "INSERT INTO students (roll_number, full_name, department, graduation_year, cgpa, active_backlogs, is_eligible) VALUES (?, ?, ?, ?, ?, ?, ?)")
                cursor.execute(q, (roll, name, dept, year, cgpa, backlogs, is_eligible))
                conn.commit()
                flash(f"Student '{name}' ({roll}) added successfully.", "success")
            except Exception as e:
                flash(f"Error saving student: {e}", "danger")
        return redirect(url_for("students"))

    with get_db() as (conn, engine):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY student_id DESC")
        all_students = cursor.fetchall()
    return render_template("students.html", students=all_students)

@app.route("/students/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    with get_db() as (conn, engine):
        cursor = conn.cursor()
        q = "DELETE FROM students WHERE student_id = %s" if engine == "mysql" else "DELETE FROM students WHERE student_id = ?"
        cursor.execute(q, (student_id,))
        conn.commit()
        flash("Student record and related placements deleted.", "info")
    return redirect(url_for("students"))

# --- Placements CRUD ---
@app.route("/placements", methods=["GET", "POST"])
@login_required
def placements():
    if request.method == "POST":
        sid = request.form.get("student_id", type=int)
        company = request.form.get("company_name", "").strip()
        role = request.form.get("role", "").strip()
        pkg = request.form.get("package_lpa", type=float)
        pdate = request.form.get("placement_date")
        status = request.form.get("status", "Offer Accepted")

        if not sid or not company or not role or pkg is None or not pdate:
            flash("All placement fields are required.", "danger")
            return redirect(url_for("placements"))

        with get_db() as (conn, engine):
            cursor = conn.cursor()
            q = ("INSERT INTO placements (student_id, company_name, role, package_lpa, placement_date, status) VALUES (%s, %s, %s, %s, %s, %s)"
                 if engine == "mysql" else
                 "INSERT INTO placements (student_id, company_name, role, package_lpa, placement_date, status) VALUES (?, ?, ?, ?, ?, ?)")
            cursor.execute(q, (sid, company, role, pkg, pdate, status))
            conn.commit()
            flash(f"Placement offer with {company} ({pkg} LPA) recorded successfully.", "success")
        return redirect(url_for("placements"))

    with get_db() as (conn, engine):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, s.roll_number, s.full_name, s.department
            FROM placements p
            JOIN students s ON p.student_id = s.student_id
            ORDER BY p.placement_id DESC
        """)
        recs = cursor.fetchall()
        cursor.execute("SELECT student_id, roll_number, full_name, department FROM students WHERE is_eligible = 1")
        eligible_students = cursor.fetchall()

    return render_template("placements.html", placements=recs, students=eligible_students)

@app.route("/placements/delete/<int:placement_id>", methods=["POST"])
@login_required
def delete_placement(placement_id):
    with get_db() as (conn, engine):
        cursor = conn.cursor()
        q = "DELETE FROM placements WHERE placement_id = %s" if engine == "mysql" else "DELETE FROM placements WHERE placement_id = ?"
        cursor.execute(q, (placement_id,))
        conn.commit()
        flash("Placement record removed.", "info")
    return redirect(url_for("placements"))

# --- Skills Tagging ---
@app.route("/skills", methods=["GET", "POST"])
@login_required
def skills():
    with get_db() as (conn, engine):
        cursor = conn.cursor()
        if request.method == "POST":
            action = request.form.get("action")
            if action == "add_skill":
                sname = request.form.get("skill_name", "").strip()
                if sname:
                    try:
                        q = "INSERT INTO skills (skill_name) VALUES (%s)" if engine == "mysql" else "INSERT INTO skills (skill_name) VALUES (?)"
                        cursor.execute(q, (sname,))
                        conn.commit()
                        flash(f"Skill '{sname}' added to registry.", "success")
                    except Exception:
                        flash(f"Skill '{sname}' already exists.", "warning")
            elif action == "tag_skill":
                sid = request.form.get("student_id", type=int)
                skid = request.form.get("skill_id", type=int)
                if sid and skid:
                    try:
                        q = "INSERT INTO student_skills (student_id, skill_id) VALUES (%s, %s)" if engine == "mysql" else "INSERT INTO student_skills (student_id, skill_id) VALUES (?, ?)"
                        cursor.execute(q, (sid, skid))
                        conn.commit()
                        flash("Skill tagged to student.", "success")
                    except Exception:
                        flash("Skill is already tagged to this student.", "warning")
            return redirect(url_for("skills"))

        cursor.execute("SELECT * FROM skills ORDER BY skill_name")
        all_skills = cursor.fetchall()
        cursor.execute("SELECT student_id, roll_number, full_name, department FROM students ORDER BY roll_number")
        all_students = cursor.fetchall()

        cursor.execute("""
            SELECT s.roll_number, s.full_name, sk.skill_name
            FROM student_skills ss
            JOIN students s ON ss.student_id = s.student_id
            JOIN skills sk ON ss.skill_id = sk.skill_id
            ORDER BY s.roll_number
        """)
        mappings = cursor.fetchall()

    return render_template("skills.html", skills=all_skills, students=all_students, mappings=mappings)

# --- Aggregated Reports (Privacy Protected) ---
@app.route("/reports")
@login_required
def reports():
    dept_stats = analytics.get_department_analysis()
    kpis = analytics.calculate_kpis()
    return render_template("reports.html", stats=dept_stats, kpis=kpis)

# --- Database Connection Settings ---
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        db_type = request.form.get("db_type", "sqlite")
        host = request.form.get("mysql_host", "localhost")
        port = request.form.get("mysql_port", type=int, default=3306)
        user = request.form.get("mysql_user", "root")
        password = request.form.get("mysql_pass", "")
        dbname = request.form.get("mysql_db", "placement_db")

        if db_type == "mysql":
            success, msg = test_mysql_connection(host=host, port=port, user=user, password=password, database=dbname)
            if success:
                database.DB_TYPE = "mysql"
                database.MYSQL_HOST = host
                database.MYSQL_PORT = port
                database.MYSQL_USER = user
                database.MYSQL_PASS = password
                database.MYSQL_DB = dbname
                init_db()
                flash("Connected to MySQL successfully! Database initialized.", "success")
            else:
                flash(f"MySQL Connection Failed: {msg}", "danger")
        else:
            database.DB_TYPE = "sqlite"
            init_db()
            flash("Switched to SQLite local database.", "info")

        return redirect(url_for("settings"))

    return render_template("settings.html", current_config={
        "db_type": database.DB_TYPE,
        "mysql_host": database.MYSQL_HOST,
        "mysql_port": database.MYSQL_PORT,
        "mysql_user": database.MYSQL_USER,
        "mysql_db": database.MYSQL_DB
    })

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", debug=True, port=5000)
