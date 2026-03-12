"""Frontend shell routing tests."""


def test_root_serves_frontend_shell(client):
    """Root path should serve the built frontend shell."""
    response = client.get("/")

    assert response.status_code == 200
    assert b'<div id="app"></div>' in response.data


def test_spa_route_falls_back_to_frontend_shell(client):
    """Non-API frontend routes should fall back to index.html."""
    response = client.get("/timers")

    assert response.status_code == 200
    assert b'<div id="app"></div>' in response.data
