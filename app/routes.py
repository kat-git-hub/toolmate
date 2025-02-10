from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
import requests
from sqlalchemy.orm import joinedload
from app.models import User, Tool
from app.forms import LoginForm, RegistrationForm
from werkzeug.security import generate_password_hash, check_password_hash

routes = Blueprint("routes", __name__, url_prefix="/")


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


@routes.route("/tool_details")
def tool_details():
    return render_template("tool_details.html", title="Details")


@routes.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
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


@routes.route("/add_tool", methods=["GET", "POST"])
@login_required
def add_tool():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price_per_day = float(request.form["price_per_day"])
        image_url = request.form["image_url"]

        new_tool = Tool(
            name=name,
            description=description,
            price_per_day=price_per_day,
            image_url=image_url,
            owner=current_user
        )

        db.session.add(new_tool)
        db.session.commit()
        
        flash("Tool successfully added!", "success")
        return redirect(url_for("routes.home"))

    return render_template("add_tool.html", title="Add Tool")


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