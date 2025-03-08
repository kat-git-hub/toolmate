import os
import uuid
import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

os.environ["FLASK_ENV"] = "testing"


@pytest.fixture(scope="session")
def app():
    """Creates a new Flask test application."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": False
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    """Creates a test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture(scope="function", autouse=True)
def reset_database(app):
    """Clears and resets the database before each test."""
    with app.app_context():
        db.session.rollback()
        db.drop_all()
        db.create_all()
        db.session.commit()


@pytest.fixture(scope="function")
def db_session(app):
    """Provides a clean database session for each test."""
    with app.app_context():
        yield db
        db.session.rollback()
        db.session.remove()


@pytest.fixture
def new_user(db_session):
    """Creates and returns a test user with a unique email."""
    user = User(
        name="Test User",
        email=f"test_{uuid.uuid4().hex}@example.com",
        password=generate_password_hash("securepassword", method="pbkdf2:sha256"),
        zip_code="10115"
    )
    db.session.add(user)
    db.session.commit()
    return user
