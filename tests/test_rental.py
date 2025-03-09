from app import db
from app.models import Tool, Rental
from datetime import datetime


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


def test_return_tool(client, new_user, db_session):
    """Test returning a rented tool."""
    
    client.post("/login", data={"email": new_user.email, "password": "securepassword"}, follow_redirects=True)

    tool = Tool(
        name="Hammer",
        description="Heavy-duty hammer",
        price_per_day=5.0,
        category="hand_tools",
        user_id=new_user.id,
        image_url="https://example.com/hammer.jpg",
        is_available=False
    )
    db_session.session.add(tool)
    db_session.session.commit()

    rental = Rental(
        tool_id=tool.id,
        renter_id=new_user.id,
        start_date=datetime(2025, 3, 1),
        end_date=datetime(2025, 3, 5)
    )
    db_session.session.add(rental)
    db_session.session.commit()

    rental_id = rental.id

    assert Rental.query.get(rental_id) is not None
    assert not tool.is_available

    response = client.post(f"/return_tool/{tool.id}", follow_redirects=True)

    returned_tool = Tool.query.get(tool.id)
    deleted_rental = Rental.query.get(rental_id)

    assert response.status_code == 200
    assert b"Tool successfully returned!" in response.data
    assert returned_tool.is_available, "Tool should be marked as available!"
    assert deleted_rental is None, "Rental record should be deleted!"