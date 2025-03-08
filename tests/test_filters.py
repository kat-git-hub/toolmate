def test_filter_tools(client):
    """Test of filtering tools by category"""
    response = client.get("/?category=Power+Tools")
    assert response.status_code == 200
    assert b"Power Tools" in response.data
