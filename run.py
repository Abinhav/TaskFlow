
import os
import uuid
import re
import smtplib
import logging

from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from email.message import EmailMessage

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_wtf.csrf import CSRFProtect

from dotenv import load_dotenv
from sqlalchemy import text

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from app.extensions import db, migrate, login_manager
from app.models import User, Task

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in (
    "true",
    "1",
    "yes"
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from the .env file.")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing from the .env file.")

app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["DEBUG"] = FLASK_DEBUG

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = not FLASK_DEBUG

csrf = CSRFProtect(app)

db.init_app(app)
migrate.init_app(app, db)

login_manager.init_app(app)
login_manager.login_view = "login"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


# Logging Configuration

LOG_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "logs"
)

os.makedirs(LOG_FOLDER, exist_ok=True)

LOG_FILE = os.path.join(LOG_FOLDER, "app.log")

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)

file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s "
        "[in %(pathname)s:%(lineno)d]"
    )
)

file_handler.setLevel(logging.INFO)

app.logger.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.info("TaskFlow application started.")
app.logger.info("Application debug mode: %s", FLASK_DEBUG)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Custom Error Handlers

@app.errorhandler(404)
def page_not_found(error):

    app.logger.warning(
        "Page not found: %s",
        request.path
    )

    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()

    app.logger.error(
        "Internal server error: %s",
        error,
        exc_info=True
    )

    return render_template("500.html"), 500


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill in all the fields.", "error")
            return redirect(url_for("contact"))

        if len(name) > 100:
            flash("Name must be less than 100 characters.", "error")
            return redirect(url_for("contact"))

        if len(email) > 254 or not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        ):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("contact"))

        if len(message) > 5000:
            flash("Message must be less than 5000 characters.", "error")
            return redirect(url_for("contact"))

        mail_username = os.getenv("MAIL_USERNAME")
        mail_password = os.getenv("MAIL_PASSWORD")
        mail_receiver = os.getenv("MAIL_RECEIVER")
        mail_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        mail_port = int(os.getenv("MAIL_PORT", "465"))

        if not mail_username or not mail_password or not mail_receiver:
            flash(
                "Email service is not configured. Please try again later.",
                "error"
            )
            return redirect(url_for("contact"))

        email_message = EmailMessage()

        email_message["Subject"] = "New TaskFlow Contact Form Feedback"
        email_message["From"] = mail_username
        email_message["To"] = mail_receiver
        email_message["Reply-To"] = email

        email_message.set_content(
            f"""
New feedback received from TaskFlow Contact Form.

Name: {name}

Email: {email}

Message:
{message}
"""
        )

        try:

            with smtplib.SMTP_SSL(
                mail_server,
                mail_port,
                timeout=15
            ) as smtp:

                smtp.login(mail_username, mail_password)
                smtp.send_message(email_message)

            app.logger.info("Contact form email sent successfully.")

            flash(
                "Your message has been sent successfully! Thank you for your feedback.",
                "success"
            )

        except (smtplib.SMTPException, OSError, ValueError):

            app.logger.exception("Contact email sending failed.")

            flash(
                "Sorry, we could not send your message. Please try again later.",
                "error"
            )

        return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            return render_template(
                "register.html",
                error="All fields are required."
            )

        if len(password) < 8:
            return render_template(
                "register.html",
                error="Password must contain at least 8 characters."
            )

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match."
            )

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return render_template(
                "register.html",
                error="Email already registered. Please login."
            )

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        app.logger.info("New user registered successfully.")

        return render_template(
            "register.html",
            success="Account created successfully! You can now login."
        )

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):

            login_user(user)

            app.logger.info("User logged in successfully.")

            return redirect(url_for("dashboard"))

        app.logger.warning("Failed login attempt.")

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# Profile Management

@app.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html",
        user=current_user
    )


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not username or not email:
            return render_template(
                "edit_profile.html",
                user=current_user,
                error="All fields are required."
            )

        if len(username) > 80:
            return render_template(
                "edit_profile.html",
                user=current_user,
                error="Username must be less than 80 characters."
            )

        if len(email) > 120 or not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        ):
            return render_template(
                "edit_profile.html",
                user=current_user,
                error="Please enter a valid email address."
            )

        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_user:
            return render_template(
                "edit_profile.html",
                user=current_user,
                error="This email address is already registered."
            )

        current_user.username = username
        current_user.email = email

        db.session.commit()

        app.logger.info("User profile updated successfully.")

        flash("Profile updated successfully!", "success")

        return redirect(url_for("profile"))

    return render_template(
        "edit_profile.html",
        user=current_user
    )


@app.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == "POST":

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_password or not new_password or not confirm_password:
            return render_template(
                "change_password.html",
                error="All fields are required."
            )

        if not check_password_hash(
            current_user.password_hash,
            current_password
        ):
            return render_template(
                "change_password.html",
                error="Current password is incorrect."
            )

        if len(new_password) < 8:
            return render_template(
                "change_password.html",
                error="New password must contain at least 8 characters."
            )

        if new_password != confirm_password:
            return render_template(
                "change_password.html",
                error="New passwords do not match."
            )

        if current_password == new_password:
            return render_template(
                "change_password.html",
                error="New password must be different from current password."
            )

        current_user.password_hash = generate_password_hash(new_password)

        db.session.commit()

        app.logger.info("User password changed successfully.")

        flash("Password changed successfully!", "success")

        return redirect(url_for("profile"))

    return render_template("change_password.html")


# Profile Picture Upload

@app.route("/profile/upload-picture", methods=["POST"])
@login_required
def upload_profile_picture():

    image_file = request.files.get("profile_image")

    if not image_file or not image_file.filename:
        flash("Please select a profile picture.", "error")
        return redirect(url_for("profile"))

    safe_filename = secure_filename(image_file.filename)

    if not safe_filename or "." not in safe_filename:
        flash("Invalid image filename.", "error")
        return redirect(url_for("profile"))

    file_extension = safe_filename.rsplit(".", 1)[-1].lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        flash("Only PNG, JPG and JPEG images are allowed.", "error")
        return redirect(url_for("profile"))

    new_image_filename = (
        f"profile_{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
    )

    upload_folder = os.path.join(
        app.static_folder,
        "images"
    )

    os.makedirs(upload_folder, exist_ok=True)

    new_image_path = os.path.join(
        upload_folder,
        new_image_filename
    )

    try:

        image_file.save(new_image_path)

        old_image_filename = current_user.profile_image

        current_user.profile_image = new_image_filename

        db.session.commit()

        if old_image_filename:

            old_image_path = os.path.join(
                upload_folder,
                old_image_filename
            )

            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        app.logger.info("User profile picture updated successfully.")

        flash("Profile picture updated successfully!", "success")

    except Exception:

        db.session.rollback()

        if os.path.exists(new_image_path):
            os.remove(new_image_path)

        app.logger.exception("Profile picture upload failed.")

        flash("Could not upload profile picture. Please try again.", "error")

    return redirect(url_for("profile"))


@app.route("/dashboard")
@login_required
def dashboard():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).order_by(Task.created_at.desc()).all()

    total_tasks = len(tasks)

    pending_tasks = sum(
        1 for task in tasks
        if task.status == "Pending"
    )

    completed_tasks = sum(
        1 for task in tasks
        if task.status == "Completed"
    )

    completion_rate = (
        round((completed_tasks / total_tasks) * 100, 1)
        if total_tasks > 0 else 0
    )

    return render_template(
        "dashboard.html",
        username=current_user.username,
        tasks=tasks,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        completion_rate=completion_rate
    )


@app.route("/tasks/create", methods=["GET", "POST"])
@login_required
def create_task():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")
        start_date_value = request.form.get("start_date", "").strip()
        due_date_value = request.form.get("due_date", "").strip()

        image_file = request.files.get("image")

        if not title:
            return render_template(
                "create_task.html",
                error="Task title is required."
            )

        if priority not in ["Low", "Medium", "High"]:
            return render_template(
                "create_task.html",
                error="Please select a valid priority."
            )

        try:
            start_date = (
                datetime.strptime(start_date_value, "%Y-%m-%d").date()
                if start_date_value else None
            )

            due_date = (
                datetime.strptime(due_date_value, "%Y-%m-%d").date()
                if due_date_value else None
            )

        except ValueError:
            return render_template(
                "create_task.html",
                error="Please enter valid dates."
            )

        if start_date and due_date and due_date < start_date:
            return render_template(
                "create_task.html",
                error="Due date cannot be earlier than start date."
            )

        image_filename = None

        if image_file and image_file.filename:

            safe_filename = secure_filename(image_file.filename)

            if not safe_filename or "." not in safe_filename:
                return render_template(
                    "create_task.html",
                    error="Invalid image filename."
                )

            file_extension = safe_filename.rsplit(".", 1)[-1].lower()

            if file_extension not in ALLOWED_EXTENSIONS:
                return render_template(
                    "create_task.html",
                    error="Only PNG, JPG and JPEG images are allowed."
                )

            image_filename = f"{uuid.uuid4().hex}.{file_extension}"

            upload_folder = os.path.join(
                app.static_folder,
                "images"
            )

            os.makedirs(upload_folder, exist_ok=True)

            image_path = os.path.join(
                upload_folder,
                image_filename
            )

            image_file.save(image_path)

        new_task = Task(
            title=title,
            description=description,
            priority=priority,
            status="Pending",
            start_date=start_date,
            due_date=due_date,
            image_filename=image_filename,
            user_id=current_user.id
        )

        db.session.add(new_task)
        db.session.commit()

        app.logger.info("New task created successfully.")

        flash("Task created successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("create_task.html")


@app.route("/tasks/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "")
        start_date_value = request.form.get("start_date", "").strip()
        due_date_value = request.form.get("due_date", "").strip()

        image_file = request.files.get("image")

        if not title:
            return render_template(
                "edit_task.html",
                task=task,
                error="Task title is required."
            )

        if priority not in ["Low", "Medium", "High"]:
            return render_template(
                "edit_task.html",
                task=task,
                error="Please select a valid priority."
            )

        try:
            start_date = (
                datetime.strptime(start_date_value, "%Y-%m-%d").date()
                if start_date_value else None
            )

            due_date = (
                datetime.strptime(due_date_value, "%Y-%m-%d").date()
                if due_date_value else None
            )

        except ValueError:
            return render_template(
                "edit_task.html",
                task=task,
                error="Please enter valid dates."
            )

        if start_date and due_date and due_date < start_date:
            return render_template(
                "edit_task.html",
                task=task,
                error="Due date cannot be earlier than start date."
            )

        new_image_filename = None

        if image_file and image_file.filename:

            safe_filename = secure_filename(image_file.filename)

            if not safe_filename or "." not in safe_filename:
                return render_template(
                    "edit_task.html",
                    task=task,
                    error="Invalid image filename."
                )

            file_extension = safe_filename.rsplit(".", 1)[-1].lower()

            if file_extension not in ALLOWED_EXTENSIONS:
                return render_template(
                    "edit_task.html",
                    task=task,
                    error="Only PNG, JPG and JPEG images are allowed."
                )

            new_image_filename = f"{uuid.uuid4().hex}.{file_extension}"

            upload_folder = os.path.join(
                app.static_folder,
                "images"
            )

            os.makedirs(upload_folder, exist_ok=True)

            new_image_path = os.path.join(
                upload_folder,
                new_image_filename
            )

            image_file.save(new_image_path)

        old_image_filename = task.image_filename

        task.title = title
        task.description = description
        task.priority = priority
        task.start_date = start_date
        task.due_date = due_date

        if new_image_filename:
            task.image_filename = new_image_filename

        db.session.commit()

        if new_image_filename and old_image_filename:

            old_image_path = os.path.join(
                app.static_folder,
                "images",
                old_image_filename
            )

            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        app.logger.info("Task updated successfully.")

        flash("Task updated successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("edit_task.html", task=task)


@app.route("/tasks/complete/<int:task_id>", methods=["POST"])
@login_required
def complete_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    if task.status == "Completed":

        flash("This task is already completed.", "info")

    else:

        task.status = "Completed"
        task.completed_at = datetime.now(timezone.utc)

        db.session.commit()

        app.logger.info("Task marked as completed.")

        flash("Task marked as completed!", "success")

    return redirect(url_for("dashboard"))


@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    if task.image_filename:

        image_path = os.path.join(
            app.static_folder,
            "images",
            task.image_filename
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(task)
    db.session.commit()

    app.logger.info("Task deleted successfully.")

    flash("Task deleted successfully!", "success")

    return redirect(url_for("dashboard"))


@app.route("/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    app.logger.info("User logged out.")

    return redirect(url_for("login"))


if __name__ == "__main__":

    with app.app_context():

        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("PostgreSQL Connected Successfully!")

    app.run(debug=FLASK_DEBUG)
