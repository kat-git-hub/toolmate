from app import db
from app.models import Tool, Rental


def test_rent_tool(client, new_user):
    """Test renting a tool."""

    client.post("/login", data={"email": new_user.email, "password": "securepassword"})

    Rental.query.delete()
    Tool.query.delete()
    db.session.commit()

    tool = Tool(
        name="Circular Saw",
        description="Strong hammer",
        price_per_day=7.0,
        category="power_tools",
        image_url="https://example.com/default_tool.jpg",
        user_id=new_user.id,
        is_available=True
    )
    db.session.add(tool)
    db.session.commit()

    response = client.post(f"/rent_tool/{tool.id}", data={
        "rental_dates": "11-03-2025 - 15-03-2025"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Tool successfully booked!" in response.data
