# 
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR, exist_ok=True)


class Config:
    """Base configuration (default)."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ Switch database depending on environment
    if os.getenv("FLASK_ENV") == "testing":
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Use in-memory DB for testing
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_DIR, 'tools.db')}"  # Production DB


class TestingConfig(Config):
    """Configuration for testing."""
    TESTING = True
    SECRET_KEY = "test_secret_key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # Disable CSRF in tests
    LOGIN_DISABLED = False  # Allow login without authentication
