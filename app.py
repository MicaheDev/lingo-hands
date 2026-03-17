from datetime import datetime
from flask import Flask, json, request, session, render_template, redirect, flash
from flask_session import Session
from helpers import login_required, apology, admin_required
import math
import os
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuración de Base de Datos para Render
# Render leerá la contraseña desde sus Variables de Entorno
uri = os.getenv("DATABASE_URL")

if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
db = SQLAlchemy(app)

# time constant to recover a life when the user lost it
RECOVERY_TIME = 1800

@app.route("/")
@login_required
def index():
    
    # get user session
    user_id = session.get("user_id")

    # get user
    user_data = db.session.execute(text("SELECT username, xp, lives, last_hearth_loss FROM users WHERE id = :id"), {"id": user_id}).mappings().all()

    # Convertir a una lista de diccionarios para no romper el template
    user_data = [dict(row) for row in user_data]

    current_lives = user_data[0]["lives"]
    last_hearth = user_data[0]["last_hearth_loss"]

    # logic to recovery lives
    if current_lives < 3 and last_hearth:
        try:
            # current date
            now = datetime.now()

            # date of when user lost last live 
            # Postgres devuelve objetos datetime reales
            last_hearth_datetime = last_hearth

            # Si por casualidad todavía llega como string, lo parseamos
            if isinstance(last_hearth_datetime, str):
                last_hearth_datetime = datetime.strptime(last_hearth, "%Y-%m-%d %H:%M:%S")

            # calculate the difference between the 2 dates and transform in seconds
            difference = now - last_hearth_datetime
            diff_seconds = difference.total_seconds()

            """
            if the difference between the two dates is greater than the recovery time or 30 minutes, 
            we calculate the lives that will be added and updated in the database.
            """
            if diff_seconds >= RECOVERY_TIME:
                # if we rounding the difference in seconds between recovery time gives us the lives to add 
                lives_to_add = math.floor(diff_seconds / RECOVERY_TIME)

                # sum it the current lives
                total_lives = current_lives + lives_to_add

                """
                if the total number of lives is greater than 3, we save 3; 
                otherwise, we save the number of lives calculated previously
                """
                new_lives = 3 if total_lives > 3 else total_lives

                # if new lives is greather then current lives mean the user no has the full lives to play we updated
                if new_lives > current_lives:

                    # if new lives is 3, return a null date; otherwise, return the current date and time to wait again
                    new_date = None if new_lives == 3 else datetime.now()

                    # update user tabel with the new data
                    db.session.execute(text("UPDATE users SET lives = :new_lives, last_hearth_loss = :new_date WHERE id = :id"), {"new_lives": new_lives, "new_date": new_date, "id": user_id})
                    db.session.commit()

                    # update current user data cited for rendering
                    user_data[0]["lives"] = new_lives
        except ValueError:
            app.logger.error("Sorry, we could calculating the new lives")


    """ 
    Hierarchy query to obtain a list within another list like this:
    units list -> modules list > levels list

    order by order_index
    """

    data = db.session.execute(text("""
        -- FIRST LEVEL: units
        SELECT COALESCE(json_agg(
            json_build_object(
                'id', u.id,
                'title', u.title,
                'order_index', u.order_index,
                'description', u.description,
                'modules', COALESCE((
                    -- SECOND LEVEL: modules
                    SELECT json_agg(
                        json_build_object(
                            'id', m.id,
                            'title', m.title,
                            'order', m.order_index,
                            'levels', COALESCE((
                                -- THIRD LEVEL: levels
                                SELECT json_agg(
                                    json_build_object(
                                        'id', l.id,
                                        'title', l.title,
                                        'order', l.order_index,
                                        'xp', l.required_xp
                                    )
                                )
                                FROM (SELECT * FROM levels WHERE module_id = m.id ORDER BY order_index) l
                            ), '[]'::json)
                        )
                    )
                    FROM (SELECT * FROM modules WHERE unit_id = u.id ORDER BY order_index) m
                ), '[]'::json)
            )
        ), '[]'::json) AS hierarchy_data
        FROM (SELECT * FROM units ORDER BY order_index) u;
    """)).mappings().all()

    # extract json 
    json_data = data[0]["hierarchy_data"]

    # transform from json to python dictionary or list
    if isinstance(json_data, str):
        hierarchy = json.loads(json_data)
    else:
        hierarchy = json_data

    # get all level IDs to know which levels the user has completed
    rows = db.session.execute(text("SELECT level_id FROM user_progress WHERE user_id = :id"), {"id": user_id}).mappings().all()
    completed_ids = [row["level_id"] for row in rows]
    
    return render_template("index.html", units=hierarchy, user_data=user_data[0], completed_ids=completed_ids)


# Lesson or level endpoint
@app.route("/lesson/<int:level_id>", methods=["GET", "POST"])
@login_required
def level(level_id):
    if request.method == "POST":
        # get user session
        user_id = session.get("user_id")

        # get all level IDs to know which levels the user has completed
        rows = db.session.execute(text("SELECT level_id FROM user_progress WHERE user_id = :id"), {"id": user_id}).mappings().all()
        completed_ids = [row["level_id"] for row in rows]

        # if the user has already completed this level, redirect to the start; do not remove lives and do not add more XP.
        if level_id in completed_ids:
            flash("Practice completed", "success")
            return redirect("/")

        # get mistakes from form
        raw_mistakes = request.form.get("mistakes")
        raw_lessons = request.form.get("lessons")

        # convert to integers
        try:
            mistakes = int(raw_mistakes)
            lessons = int(raw_lessons)
        except ValueError:
            mistakes = 0
            lessons = 0

        # calculate the hits
        success = lessons - mistakes

        if lessons > 0:
            """
            if the errors are greater than or equal to the number of correct answers, 
            we take the user's heart and record the date and time the user lost their heart.

            otherwise, we will add XP to the user to unlock the next levels.
            """
            if mistakes >= success:
                now = datetime.now()
                db.session.execute(text("UPDATE users SET lives = lives - 1, last_hearth_loss = :date WHERE id = :id"), {"date": now, "id": user_id})
                db.session.commit()
                flash("You lost :(", "error")

            else:
                db.session.execute(text("UPDATE users SET xp = xp + 1 WHERE id = :id"), {"id": user_id})
                db.session.execute(text("INSERT INTO user_progress (user_id, level_id) VALUES (:id, :level_id)"), {"id": user_id, "level_id": level_id})
                db.session.commit()
                flash("Good Work :)", "success")


        return redirect("/")

    else:
        # get user data
        user_id = session.get("user_id")

        # get user xp, lives and username to use and render on template
        user_data = db.session.execute(text("SELECT username, xp, lives FROM users WHERE id = :id"), {"id": user_id}).mappings().all()
        
        # Convert to dictionary
        user_dict = dict(user_data[0])

        # get level data
        level_data = db.session.execute(text("SELECT required_xp FROM levels WHERE id = :id"), {"id": level_id}).mappings().all()

        # check if the user has the required XP for the level; if not, redirect to the index
        if user_dict["xp"] < level_data[0]["required_xp"]:
            flash("You don't have enough experience to take this level", "error")
            return redirect("/")

        # check if the user ran out of lives
        if user_dict["lives"] == 0:
            flash("You don't have lives wait 30 minutes", "error")
            return redirect("/")

        # the content of the level or all the lessons of the level; this will be used by the react js component.
        level_content = db.session.execute(text("SELECT * FROM level_content WHERE level_id = :id ORDER BY order_index"), {"id": level_id}).mappings().all()
        level_content = [dict(row) for row in level_content]

        return render_template("level.html", level_content=level_content, user_data=user_dict)


@app.route("/dashboard")
@admin_required
def dashboard():
    """ 
    Hierarchy query to obtain a list within another list like this:
    units list -> modules list > levels list > level_content list

    order by order_index

    This grouping is for managing, deleting, and adding parts of the course such as modules, units, levels, etc.
    """
    data = db.session.execute(text("""
        -- FIRST LEVEL: units
        SELECT COALESCE(json_agg(
            json_build_object(
                'id', u.id,
                'title', u.title,
                'order_index', u.order_index,
                'description', u.description,
                'modules', COALESCE((
                    -- SECOND LEVEL: mdoules
                    SELECT json_agg(
                        json_build_object(
                            'id', m.id,
                            'title', m.title,
                            'order', m.order_index,
                            'levels', COALESCE((
                                -- THIRD LEVEL: levels
                                SELECT json_agg(
                                    json_build_object(
                                        'id', l.id,
                                        'title', l.title,
                                        'order', l.order_index,
                                        'xp', l.required_xp,
                                        'content', COALESCE((
                                            -- FOURTH LEVEL: level_content
                                            SELECT json_agg(
                                                json_build_object(
                                                    'id', c.id,
                                                    'type', c.step_type,
                                                    'sign_id', c.sign_id,
                                                    'meaning', c.meaning,
                                                    'instructions', c.instructions,
                                                    'option_a', c.option_a,
                                                    'option_b', c.option_b,
                                                    'option_c', c.option_c,
                                                    'correct', c.correct_option,
                                                    'order', c.order_index
                                                )
                                            )
                                            FROM (SELECT * FROM level_content WHERE level_id = l.id ORDER BY order_index) c
                                        ), '[]'::json)
                                    )
                                )
                                FROM (SELECT * FROM levels WHERE module_id = m.id ORDER BY order_index) l
                            ), '[]'::json)
                        )
                    )
                    FROM (SELECT * FROM modules WHERE unit_id = u.id ORDER BY order_index) m
                ), '[]'::json)
            )
        ), '[]'::json) AS hierarchy_data
        FROM (SELECT * FROM units ORDER BY order_index) u;
    """)).mappings().all()
    
    # extract json 
    json_data = data[0]["hierarchy_data"]
    
    # transform from json to python dictionary or list
    if isinstance(json_data, str):
        hierarchy = json.loads(json_data)
    else:
        hierarchy = json_data
    
    return render_template("dashboard.html", units=hierarchy)


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        """Log user in"""
        # Forget any user_id
        session.clear()

        username = request.form.get("username")
        password = request.form.get("password")

        # User reached route via POST (as by submitting a form via POST)
        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not password:
            return apology("must provide password", 400)

        # Query database for username
        rows = db.session.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username}).mappings().all()
        rows = [dict(row) for row in rows]

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], password
        ):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        # Save the user role for administrator routes
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        session["role"] = rows[0]["role"]

        # Redirect user to home page
        return redirect("/")
    
    else: 
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)

        if not password:
            return apology("must provide password", 400)
        
        if not confirmation:
            return apology("must provide confirmation", 400)
        
        # If the password and confirmation are not the same, send an apology.
        if password != confirmation:
            return apology("passwords are not the same", 400)
        
        # generate hash
        hash = generate_password_hash(password)

        try:
            # insert new user
            db.session.execute(text("INSERT INTO users (username, hash, role) VALUES (:username, :hash, 'user')"), {"username": username, "hash": hash})
            db.session.commit()

            flash("Register was succesfull", "success")
            return redirect("/login")
        
        except Exception:
            db.session.rollback()
            return apology("username already taken", 409)
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# This route is for adding new cour
@app.route("/api/units", methods=["POST"])
@admin_required
def units():

    title = request.form.get("title")
    description = request.form.get("description")

    if not title:
        return apology("must provide title", 400)
    
    if not description:
        return apology("must provide description", 400)

    # This query gets the maximum order_index to calculate the next index of the new unit
    raw_index = db.session.execute(text("SELECT COALESCE(MAX(order_index), 0) + 1 AS next_index FROM units")).mappings().all()

    # transform into an integer
    try:
        new_index = int(raw_index[0]["next_index"]) 
    except ValueError:
        return apology("Error adding the unit", 500)

    # Add the new unit for the course
    db.session.execute(text("INSERT INTO units (title, description, order_index) VALUES (:title, :description, :new_index)"), {"title": title, "description": description, "new_index": new_index})
    db.session.commit()

    return redirect("/dashboard")

# this route only delete units by id
@app.route("/api/units/delete/<int:unit_id>", methods=["POST"])
@admin_required
def delete_unit(unit_id):

    if not unit_id:
        return apology("must provide unit_id", 400)
    
    try:
        db.session.execute(text("DELETE FROM units WHERE id = :id"), {"id": unit_id})
        db.session.commit()
    except Exception:
        db.session.rollback()
        return apology("can't delete content of this unit", 501)

    return redirect("/dashboard")

# This route is for adding new modules to the course
@app.route("/api/modules", methods=["POST"])
@admin_required
def modules():

    unit_id = request.form.get("unit_id")
    title = request.form.get("title")

    # check if the unit exists before adding the new module
    if not unit_id:
        return apology("must provide unit_id", 400)
    
    rows = db.session.execute(text("SELECT * FROM units WHERE id = :id"), {"id": unit_id}).mappings().all()

    if len(rows) != 1:
        return apology("unit_id don't exist in database", 404)
    
    if not title:
        return apology("must provide title", 400)
    
    # This query gets the maximum order_index to calculate the next index of the new module
    raw_index = db.session.execute(text("SELECT COALESCE(MAX(order_index), 0) + 1 AS next_index FROM modules")).mappings().all()

    # transform into an integer
    try:
        new_index = int(raw_index[0]["next_index"]) 
    except ValueError:
        return apology("Error adding the module", 500)

    # Add the new module for the course
    db.session.execute(text("INSERT INTO modules (unit_id, title, order_index) VALUES (:unit_id, :title, :new_index)"), {"unit_id": unit_id, "title": title, "new_index": new_index})
    db.session.commit()

    return redirect("/dashboard")

# this route only delete module by id
@app.route("/api/modules/delete/<int:module_id>", methods=["POST"])
@admin_required
def delete_module(module_id):

    if not module_id:
        return apology("must provide module_id", 400)
    try:
        db.session.execute(text("DELETE FROM modules WHERE id = :id"), {"id": module_id})
        db.session.commit()
    except Exception:
        db.session.rollback()
        return apology("can't delete content of this module", 501)

    return redirect("/dashboard")


# This route is for adding new levels to the course  
@app.route("/api/levels", methods=["POST"])
@admin_required
def levels():

    module_id = request.form.get("module_id")
    title = request.form.get("title")
    raw_xp = request.form.get("required_xp")
    
    # check if the module exists before adding the new level
    if not module_id:
        return apology("must provide module_id", 400)
    
    rows = db.session.execute(text("SELECT * FROM modules WHERE id = :id"), {"id": module_id}).mappings().all()

    if len(rows) != 1:
        return apology("module_id don't exist in database", 404)
    
    if not title:
        return apology("must provide title", 400)
    
    # This query gets the maximum order_index to calculate the next index of the new level
    raw_index = db.session.execute(text("SELECT COALESCE(MAX(order_index), 0) + 1 AS next_index FROM levels")).mappings().all()

    # transform into an integer
    try:
        new_index = int(raw_index[0]["next_index"]) 
    except ValueError:
        return apology("Error adding the module", 500)
    
    # check the admin introduce a rquired_xp
    if not raw_xp and raw_xp != 0:
        return apology("must provide required_xp", 400)
    
    # transform into an integer
    try:
        required_xp = int(raw_xp)
    except ValueError:
        return apology("required_xp is not a valid number", 400)

    if required_xp < 0:
        return apology("required_xp must be 0 or positive integer",400)

    # Add the new level for the course
    db.session.execute(text("INSERT INTO levels (module_id, title, order_index, required_xp) VALUES (:module_id, :title, :new_index, :required_xp)"), {"module_id": module_id, "title": title, "new_index": new_index, "required_xp": required_xp})
    db.session.commit()

    return redirect("/dashboard")

# this route only delete levels by id
@app.route("/api/levels/delete/<int:level_id>", methods=["POST"])
@admin_required
def delete_level(level_id):

    if not level_id:
        return apology("must provide level_id", 400)
    try:
        db.session.execute(text("DELETE FROM levels WHERE id = :id"), {"id": level_id})
        db.session.commit()
    except Exception:
        db.session.rollback()
        return apology("can't delete content of this level", 501)

    return redirect("/dashboard")


@app.route("/api/levels/level-content", methods=["POST"])
@admin_required
def level_content():
    level_id = request.form.get("level_id")
    step_type = request.form.get("step_type")
    sign_id = request.form.get("sign_id")
    meaning = request.form.get("meaning")
    instructions = request.form.get("intructions")
    op_a = request.form.get("option_a")
    op_b = request.form.get("option_b")
    op_c = request.form.get("option_c")
    correct_op = request.form.get("correct_option")

    # check if the level exists before adding the new level_content
    if not level_id:
        return apology("must provide level_id", 400)
    
    rows = db.session.execute(text("SELECT * FROM levels WHERE id = :id"), {"id": level_id}).mappings().all()

    if len(rows) != 1:
        return apology("level_id don't exist in database", 404)
    
    # validate that step type exists and is valid
    if not step_type or (step_type != "learn" and step_type != "quiz"):
        return apology("provide step_type or this have invalid value", 400)
    
    if not sign_id:
        return apology("must provide sign_id",400)
    
    # This query gets the maximum order_index to calculate the next index of the new level_content
    raw_index = db.session.execute(text("SELECT COALESCE(MAX(order_index), 0) + 1 AS next_index FROM level_content")).mappings().all()

    # transform into an integer
    try:
        new_index = int(raw_index[0]["next_index"]) 
    except ValueError:
        return apology("Error adding the module", 500)

    # Add the new level_content for the course
    db.session.execute(text("""
    INSERT INTO level_content 
        (level_id, step_type, sign_id, meaning, instructions, option_a, option_b, option_c, correct_option, order_index) 
            VALUES (:level_id, :step_type, :sign_id, :meaning, :instructions, :op_a, :op_b, :op_c, :correct_op, :new_index)
    """), {
        "level_id": level_id,
        "step_type": step_type,
        "sign_id": sign_id,
        "meaning": meaning,
        "instructions": instructions,
        "op_a": op_a,
        "op_b": op_b,
        "op_c": op_c,
        "correct_op": correct_op,
        "new_index": new_index
    })
    db.session.commit()

    return redirect("/dashboard")

# this route only delete level_content by id
@app.route("/api/levels/level-content/delete/<int:level_content_id>", methods=["POST"])
@admin_required
def delete_level_content(level_content_id):

    if not level_content_id:
        return apology("must provide level_content_id", 400)
    
    db.session.execute(text("DELETE FROM level_content WHERE id = :id"), {"id": level_content_id})
    db.session.commit()

    return redirect("/dashboard")
