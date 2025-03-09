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


def test_edit_tool(client, new_user, db_session):
    """Test editing an existing tool."""
    client.post("/login", data={"email": new_user.email, "password": "securepassword"}, follow_redirects=True)

    tool = Tool(
        name="Old Name",
        description="Old Description",
        price_per_day=5.0,
        category="hand_tools",
        user_id=new_user.id,
        image_url="https://example.com/tool.jpg",
        is_available=True
    )
    db_session.session.add(tool)
    db_session.session.commit()

    response = client.post(f"/edit_tool/{tool.id}", data={
        "name": "Updated Name",
        "description": "Updated Description",
        "price_per_day": "8",
        "category": "power_tools"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Tool updated successfully" in response.data


def test_delete_tool(client, new_user, db_session,app):
    """Test deleting a tool."""
    client.post("/login", data={"email": new_user.email, "password": "securepassword"}, follow_redirects=True)

    tool = Tool(
        name="Delete Me",
        description="This tool will be deleted",
        price_per_day=7.5,
        category="gardening_tools",
        user_id=new_user.id,
        image_url="https://example.com/tool.jpg",
        is_available=True
    )
    db_session.session.add(tool)
    db_session.session.commit()

    tool_id = tool.id

    assert Tool.query.get(tool_id) is not None

    response = client.post(f"/delete_tool/{tool_id}", follow_redirects=True)

    with app.app_context():
        deleted_tool = Tool.query.get(tool_id)

    assert response.status_code == 200
    assert b"Tool deleted successfully!" in response.data
    assert deleted_tool is None, "Tool was not deleted from the database!"
