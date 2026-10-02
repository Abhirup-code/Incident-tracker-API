def test_health_check(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
