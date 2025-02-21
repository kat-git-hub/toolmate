import os
import requests
from app import db
from app.models import User, Tool
from app.forms import LoginForm, RegistrationForm, ToolForm
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user


routes = Blueprint("routes", __name__, url_prefix="/")

UPLOAD_FOLDER = "static/images"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


@routes.route("/")
def home():
    tools = Tool.query.all()
    users = User.query.options(joinedload(User.tools)).filter(
        User.latitude.isnot(None), User.longitude.isnot(None)
    ).all()
    users_data = [{
        "name": user.name,
        "zip_code": user.zip_code if user.zip_code else "",
        "latitude": user.latitude if user.latitude is not None else 0,
        "longitude": user.longitude if user.longitude is not None else 0,
        "tools": [{"id": tool.id, "name": tool.name, "price_per_day": tool.price_per_day} for tool in user.tools]
    } for user in users]
    
    return render_template("index.html", tools=tools, users=users_data)


@routes.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("routes.home"))
        else:
            flash("Invalid email or password.", "danger")
    
    return render_template("login.html", title="Sign In", form=form)


@routes.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        zip_code = form.zip_code.data

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        latitude, longitude = get_coordinates(zip_code)
        if latitude is None or longitude is None:
            flash("Error: Failed to find coordinates by ZIP code", "danger")
            return redirect(url_for("routes.register"))
        if User.query.filter_by(email=email).first():
            flash("This email is already registered. Try logging in", "warning")
            return redirect(url_for("routes.login"))

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            zip_code=zip_code,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Registration successful! Welcome to ToolMate!", "success")
        return redirect(url_for("routes.home"))

    return render_template("registration.html", title="Registration", form=form)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@routes.route("/add_tool", methods=["GET", "POST"])
@login_required
def add_tool():
    form = ToolForm()
    
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        price_per_day = form.price_per_day.data
        category = form.category.data
        file = request.files["image"]

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            image_url = f"/{filepath}"

        else:
            flash("Invalid file! Only PNG, JPG, JPEG, and GIF formats are allowed.", "danger")
            return redirect(url_for("routes.add_tool"))

        new_tool = Tool(
            name=name,
            description=description,
            price_per_day=price_per_day,
            category=category,
            image_url=image_url,
            owner=current_user
        )

        db.session.add(new_tool)
        db.session.commit()

        flash("The tool has been successfully added!", "success")
        return redirect(url_for("routes.home"))

    return render_template("add_tool.html", title="Add Tool", form=form)


@routes.route("/my_tools")
@login_required
def my_tools():
    tools = Tool.query.filter_by(user_id=current_user.id).all()
    return render_template("my_tools.html", tools=tools)


@routes.route("/edit_tool/<int:tool_id>", methods=["GET", "POST"])
@login_required
def edit_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)

    if tool.user_id != current_user.id:
        flash("You are not authorized to edit this tool.", "danger")
        return redirect(url_for("routes.my_tools"))

    if request.method == "POST":
        tool.name = request.form["name"]
        tool.description = request.form["description"]
        tool.price_per_day = float(request.form["price_per_day"])

        file = request.files.get("image")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join("static/images", filename)
            file.save(filepath)
            tool.image_url = f"/static/images/{filename}"

        db.session.commit()
        flash("Tool updated successfully!", "success")
        return redirect(url_for("routes.my_tools"))

    return render_template("edit_tool.html", tool=tool)


@routes.route("/delete_tool/<int:tool_id>", methods=["POST"])
@login_required
def delete_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)

    if tool.user_id != current_user.id:
        flash("You are not authorized to delete this tool.", "danger")
        return redirect(url_for("routes.my_tools"))

    db.session.delete(tool)
    db.session.commit()
    flash("Tool deleted successfully!", "success")
    return redirect(url_for("routes.my_tools"))


@routes.route("/tool/<int:tool_id>")
def tool_details(tool_id):
    tool = Tool.query.get(tool_id)
    if not tool:
        flash("Requested tool not found.", "warning")
        return redirect(url_for("routes.home"))
    return render_template("tool_details.html", tool=tool)

@routes.route("/rent_tool/<int:tool_id>", methods=["POST"])
@login_required
def rent_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)

    if not tool.is_available:
        flash("This tool is already rented!", "warning")
        return redirect(url_for("routes.home"))

    # Block
    tool.is_available = False
    db.session.commit()

    flash(f"You have rented {tool.name}!", "success")
    return redirect(url_for("routes.home"))


@routes.route("/return_tool/<int:tool_id>", methods=["POST"])
@login_required
def return_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)

    #is available
    tool.is_available = True
    db.session.commit()

    flash(f"{tool.name} has been returned and is available for rent!", "info")
    return redirect(url_for("routes.home"))



@routes.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("routes.home"))

# @routes.route("/add_test_user")
# def add_test_user():
#     test_user = User(
#         name="Test User",
#         email="test@example.com",
#         password="hashed_password_here",
#         zip_code="10115"
#     )
    
#    
#     test_user.latitude, test_user.longitude = get_coordinates(test_user.zip_code)

#     db.session.add(test_user)
#     db.session.commit()
#     flash("Test user added!", "success")

#     return redirect(url_for("routes.home"))



def get_coordinates(zip_code):
    url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&format=json"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    
    if response.status_code == 200 and response.json():
        location = response.json()[0]
        return float(location["lat"]), float(location["lon"])
    
    return None, None  # If couldn't find the coordinates