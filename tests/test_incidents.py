

def create_sample_incident(client, **overrides):
    payload = {
        "title": "Deployment pipeline failure",
        "service": "ci-cd",
        "severity": "medium",
        "description": "GitHub Actions job failed on the build step",
    }
    payload.update(overrides)
    return client.post("/incidents", json=payload)


class TestCreateIncident:
    def test_create_incident_success(self, client):
        response = create_sample_incident(client)
        assert response.status_code == 201
        body = response.get_json()
        assert body["title"] == "Deployment pipeline failure"
        assert body["status"] == "open"
        assert body["resolved_at"] is None

    def test_create_incident_missing_title(self, client):
        response = client.post("/incidents", json={"service": "ci-cd"})
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_create_incident_missing_service(self, client):
        response = client.post("/incidents", json={"title": "No service given"})
        assert response.status_code == 400

    def test_create_incident_invalid_severity(self, client):
        response = create_sample_incident(client, severity="apocalyptic")
        assert response.status_code == 400

    def test_create_incident_default_severity(self, client):
        response = client.post("/incidents", json={"title": "Minor issue", "service": "web"})
        assert response.status_code == 201
        assert response.get_json()["severity"] == "low"


class TestListIncidents:
    def test_list_empty(self, client):
        response = client.get("/incidents")
        assert response.status_code == 200
        assert response.get_json() == []

    def test_list_returns_created_incidents(self, client):
        create_sample_incident(client)
        create_sample_incident(client, title="Second incident", service="api")

        response = client.get("/incidents")
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_list_filter_by_status(self, client):
        r = create_sample_incident(client)
        incident_id = r.get_json()["id"]
        client.patch(f"/incidents/{incident_id}", json={"status": "resolved"})
        create_sample_incident(client, title="Still open")

        response = client.get("/incidents?status=resolved")
        assert response.status_code == 200
        body = response.get_json()
        assert len(body) == 1
        assert body[0]["status"] == "resolved"

    def test_list_filter_by_severity(self, client):
        create_sample_incident(client, severity="critical")
        create_sample_incident(client, severity="low")

        response = client.get("/incidents?severity=critical")
        assert len(response.get_json()) == 1


class TestGetIncident:
    def test_get_existing_incident(self, client):
        r = create_sample_incident(client)
        incident_id = r.get_json()["id"]

        response = client.get(f"/incidents/{incident_id}")
        assert response.status_code == 200
        assert response.get_json()["id"] == incident_id

    def test_get_nonexistent_incident(self, client):
        response = client.get("/incidents/9999")
        assert response.status_code == 404


class TestUpdateIncident:
    def test_update_status_to_resolved_sets_timestamp(self, client):
        r = create_sample_incident(client)
        incident_id = r.get_json()["id"]

        response = client.patch(f"/incidents/{incident_id}", json={"status": "resolved"})
        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "resolved"
        assert body["resolved_at"] is not None

    def test_reopening_clears_resolved_timestamp(self, client):
        r = create_sample_incident(client)
        incident_id = r.get_json()["id"]
        client.patch(f"/incidents/{incident_id}", json={"status": "resolved"})

        response = client.patch(f"/incidents/{incident_id}", json={"status": "open"})
        assert response.get_json()["resolved_at"] is None

    def test_update_invalid_status(self, client):
        r = create_sample_incident(client)
        incident_id = r.get_json()["id"]

        response = client.patch(f"/incidents/{incident_id}", json={"status": "not-a-real-status"})
        assert response.status_code == 400

    def test_update_nonexistent_incident(self, client):
        response = client.patch("/incidents/9999", json={"status": "resolved"})
        assert response.status_code == 404

    def test_update_severity(self, client):
        r = create_sample_incident(client, severity="low")
        incident_id = r.get_json()["id"]

        response = client.patch(f"/incidents/{incident_id}", json={"severity": "critical"})
        assert response.get_json()["severity"] == "critical"


class TestDeleteIncident:
    def test_delete_existing_incident(self, client):
        r = create_sample_incident(client)
        incident_id = r.get_json()["id"]

        response = client.delete(f"/incidents/{incident_id}")
        assert response.status_code == 204

        follow_up = client.get(f"/incidents/{incident_id}")
        assert follow_up.status_code == 404

    def test_delete_nonexistent_incident(self, client):
        response = client.delete("/incidents/9999")
        assert response.status_code == 404


class TestStats:
    def test_stats_on_empty_db(self, client):
        response = client.get("/incidents/stats")
        assert response.status_code == 200
        body = response.get_json()
        assert body["total"] == 0

    def test_stats_counts_correctly(self, client):
        create_sample_incident(client, severity="high")
        create_sample_incident(client, severity="high")
        create_sample_incident(client, severity="low")

        response = client.get("/incidents/stats")
        body = response.get_json()
        assert body["total"] == 3
        assert body["by_severity"]["high"] == 2
        assert body["by_severity"]["low"] == 1
