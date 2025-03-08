import io
import uuid
from app.models import User, Tool
from app import db
from werkzeug.security import generate_password_hash


def test_add_tool(client, app):
    """Test adding a tool with an image upload."""
    
    test_email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"

    with app.app_context():
        test_user = User(
            name="Test User",
            email=test_email,
            zip_code="10115",
            password=generate_password_hash("securepassword")
        )
        db.session.add(test_user)
        db.session.commit()

    with client:
        login_response = client.post("/login", data={
            "email": test_email,
            "password": "securepassword"
        }, follow_redirects=True)

        assert login_response.status_code == 200, "Login failed!"

        with client.session_transaction() as session:
            assert "_user_id" in session, "Login session is missing user_id!"

        with app.app_context():
            test_user = User.query.filter_by(email=test_email).first()
            assert test_user is not None, "Test user was not created!"
            assert test_user.id is not None, "Test user ID is missing!"

        fake_image = io.BytesIO(b"fake image data")

        response = client.post("/add_tool", data={
            "name": "Test Drill",
            "description": "Temporary test drill",
            "price_per_day": "10.5",
            "category": "power_tools",
            "user_id": test_user.id,
            "image": (fake_image, "test_image.jpg")
        }, content_type="multipart/form-data", follow_redirects=True)

        with app.app_context():
            added_tool = Tool.query.filter_by(name="Test Drill").first()

        assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
        assert b"The tool has been successfully added!" in response.data, "Flash message missing!"
