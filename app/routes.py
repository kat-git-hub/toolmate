import os
import requests
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash
)
from flask_login import (
    login_user, logout_user, login_required,
    current_user
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload
from app import db
from app.models import User, Tool, Rental
from app.forms import LoginForm, RegistrationForm, ToolForm
from sqlalchemy import and_

routes = Blueprint("routes", __name__, url_prefix="/")

UPLOAD_FOLDER = "static/images"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


@routes.route("/", methods=["GET"])
def home():
    page = request.args.get("page", 1, type=int)
    per_page = 6

    # Read filter inputs from query parameters
    search = request.args.get("search", "", type=str)
    category = request.args.get("category", "", type=str)
    min_price = request.args.get("min_price", 0.0, type=float)
    max_price = request.args.get("max_price", 9999.0, type=float)
    availability = request.args.get("availability", "all", type=str)

    query = Tool.query

    if search:
        query = query.filter(Tool.name.ilike(f"%{search}%"))

    if category and category != "all":
        query = query.filter_by(category=category)

    query = query.filter(and_(Tool.price_per_day >= min_price, Tool.price_per_day <= max_price))

    if availability == "available":
        query = query.filter_by(is_available=True)
    elif availability == "unavailable":
        query = query.filter_by(is_available=False)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    tools = pagination.items

    users = User.query.options(joinedload(User.tools)).filter(
        User.latitude.isnot(None), User.longitude.isnot(None)
    ).all()

    users_data = [
        {
            "name": user.name,
            "zip_code": user.zip_code or "",
            "latitude": user.latitude or 0,
            "longitude": user.longitude or 0,
            "tools": [
                {"id": tool.id, "name": tool.name, "price_per_day": tool.price_per_day}
                for tool in user.tools
            ],
        }
        for user in users
    ]

    return render_template("index.html", tools=tools, users=users_data, pagination=pagination)


@routes.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("routes.home"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html", title="Sign In", form=form)


@routes.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        if User.query.filter_by(email=email).first():
            flash("This email is already registered. Try logging in.", "warning")
            return redirect(url_for("routes.login"))

        hashed_password = generate_password_hash(form.password.data, method="pbkdf2:sha256")
        latitude, longitude = get_coordinates(form.zip_code.data)
        if latitude is None or longitude is None:
            flash("Error: Failed to find coordinates by ZIP code.", "danger")
            return redirect(url_for("routes.register"))

        new_user = User(
            name=form.name.data,
            email=email,
            password=hashed_password,
            zip_code=form.zip_code.data,
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
        file = request.files.get("image")
        if not file or not allowed_file(file.filename):
            flash("Invalid file! Only PNG, JPG, JPEG formats are allowed.", "danger")
            return redirect(url_for("routes.add_tool"))

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        image_url = f"/{filepath}"

        new_tool = Tool(
            name=form.name.data,
            description=form.description.data,
            price_per_day=form.price_per_day.data,
            category=form.category.data,
            user_id=int(current_user.id),
            image_url=image_url,
            is_available=True
        )
        db.session.add(new_tool)
        db.session.commit()
        flash("The tool has been successfully added!", "success")
        return redirect(url_for("routes.home"))

    return render_template("add_tool.html", title="Add Tool", form=form)


@routes.route("/my_tools")
@login_required
def my_tools():
    """Show user's owned and rented tools."""
    owned_tools = Tool.query.filter_by(user_id=current_user.id).all()
    # Get tools rented by the user
    rented_tools = db.session.query(Tool).join(Rental).filter(
        Rental.renter_id == current_user.id
    ).all()

    return render_template("my_tools.html", owned_tools=owned_tools, rented_tools=rented_tools)


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
        tool.category = request.form["category"]

        file = request.files.get("image")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            tool.image_url = f"/{filepath}"

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
    tool = Tool.query.get_or_404(tool_id)
    return render_template("tool_details.html", tool=tool)


@routes.route("/rent_tool/<int:tool_id>", methods=["POST"])
@login_required
def rent_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    rental_dates = request.form.get("rental_dates")
    if not rental_dates:
        flash("Please select rental dates.", "danger")
        return redirect(url_for("routes.tool_details", tool_id=tool_id))

    try:
        start_date, end_date = [
            datetime.strptime(date, "%d-%m-%Y").date()
            for date in rental_dates.split(" - ")
        ]
        if start_date >= end_date:
            flash("Invalid rental period. Please select valid dates.", "danger")
            return redirect(url_for("routes.tool_details", tool_id=tool_id))

        overlapping_rental = Rental.query.filter(
            Rental.tool_id == tool_id,
            Rental.start_date <= end_date,
            Rental.end_date >= start_date
        ).first()

        if overlapping_rental:
            flash("This tool is already booked for the selected dates.", "danger")
            return redirect(url_for("routes.tool_details", tool_id=tool_id))

        rental = Rental(
            tool_id=tool.id,
            renter_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(rental)
        tool.is_available = False
        db.session.commit()

        flash("Tool successfully booked!", "success")
        return redirect(url_for("routes.home"))
    except ValueError:
        flash("Invalid date format. Please select dates again.", "danger")
        return redirect(url_for("routes.tool_details", tool_id=tool_id))


@routes.route("/return_tool/<int:tool_id>", methods=["POST"])
@login_required
def return_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    rental = Rental.query.filter_by(
        tool_id=tool.id, renter_id=current_user.id
    ).order_by(Rental.id.desc()).first()

    if rental:
        db.session.delete(rental)
        tool.is_available = True
        db.session.commit()
        flash("Tool successfully returned!", "success")
    else:
        flash("You haven't rented this tool.", "danger")

    return redirect(url_for("routes.home"))


@routes.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("routes.home"))


def get_coordinates(zip_code):
    url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&format=json"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code == 200 and response.json():
        location = response.json()[0]
        return float(location["lat"]), float(location["lon"])
    return None, None
