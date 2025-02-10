import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR, exist_ok=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    SQLALCHEMY_DATABASE_URI = f"sqlite:////{os.path.join(INSTANCE_DIR, 'tools.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

