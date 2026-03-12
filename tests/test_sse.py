"""SSE route tests."""


def test_stream_rejects_query_string_token(client, test_user_token):
    """SSE endpoint must not accept JWT in the query string."""
    response = client.get(f"/api/stream?token={test_user_token}")

    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "Missing authorization token"
