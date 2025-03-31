from app import db
from flask_login import UserMixin


class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price_per_day = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=False, default="https://example.com/default_tool.jpg")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_tool_user_id"), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    rentals = db.relationship("Rental", backref="tool", lazy=True)

    def __init__(self, name, description, price_per_day, category, user_id, image_url, is_available=True):
        if not user_id:
            raise ValueError("Tool must be associated with a user!")
        self.name = name
        self.description = description
        self.price_per_day = price_per_day
        self.category = category
        self.user_id = user_id
        self.image_url = image_url
        self.is_available = is_available


class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey("tool.id"), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    renter = db.relationship("User", backref="rentals")


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    zip_code = db.Column(db.String(10), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    tools = db.relationship("Tool", backref="owner", lazy=True)
