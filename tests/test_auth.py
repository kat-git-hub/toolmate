import uuid
from app.models import User
from app import db
from werkzeug.security import generate_password_hash


def test_register(client, app):
    """Test user registration with a unique email."""
    unique_email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    password = "securepassword"

    response = client.post("/register", data={
        "name": "New User",
        "email": unique_email,
        "zip_code": "10115",
        "password": password,
        "password2": password
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Registration successful! Welcome to ToolMate!" in response.data

    user = User.query.filter_by(email=unique_email).first()
    if user:
        db.session.delete(user)
        db.session.commit()


def test_login(client, new_user):
    """Test user login."""
    response = client.post("/login", data={
        "email": new_user.email,
        "password": "securepassword"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Login successful!" in response.data

def test_register_missing_field(client):
    """Test user registration with missing fields."""
    response = client.post("/register", data={
        "name": "",
        "email": "user@example.com",
        "zip_code": "10115",
        "password": "password",
        "password2": "password"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"This field is required" in response.data


def test_login_invalid_password(client, new_user):
    """Test login with invalid password."""
    response = client.post("/login", data={
        "email": new_user.email,
        "password": "wrongpassword"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data
