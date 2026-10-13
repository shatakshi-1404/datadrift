import io


def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_project(client):
    create = client.post("/api/projects", json={"name": "Test Project"})
    assert create.status_code == 201
    project_id = create.json()["id"]

    fetched = client.get(f"/api/projects/{project_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Test Project"


def _csv_bytes(content: str) -> io.BytesIO:
    return io.BytesIO(content.encode("utf-8"))


def test_dataset_upload_rejects_non_csv(client):
    project = client.post("/api/projects", json={"name": "P"}).json()
    response = client.post(
        f"/api/projects/{project['id']}/datasets/upload",
        files={"file": ("notes.txt", _csv_bytes("hello"), "text/plain")},
        data={"dataset_type": "reference"},
    )
    assert response.status_code == 422


def test_dataset_upload_accepts_a_valid_csv(client):
    project = client.post("/api/projects", json={"name": "P"}).json()
    csv_content = "age,plan,churn\n25,monthly,0\n40,yearly,1\n"
    response = client.post(
        f"/api/projects/{project['id']}/datasets/upload",
        files={"file": ("reference.csv", _csv_bytes(csv_content), "text/csv")},
        data={"dataset_type": "reference"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["rows"] == 2
    assert "file_path" not in body


def test_monitoring_run_end_to_end(client):
    project = client.post("/api/projects", json={"name": "P"}).json()

    reference_csv = "age,plan\n" + "\n".join(f"{20 + i},monthly" for i in range(30))
    current_csv = "age,plan\n" + "\n".join(f"{60 + i},yearly" for i in range(30))

    ref = client.post(
        f"/api/projects/{project['id']}/datasets/upload",
        files={"file": ("reference.csv", _csv_bytes(reference_csv), "text/csv")},
        data={"dataset_type": "reference"},
    ).json()
    cur = client.post(
        f"/api/projects/{project['id']}/datasets/upload",
        files={"file": ("current.csv", _csv_bytes(current_csv), "text/csv")},
        data={"dataset_type": "current"},
    ).json()

    run_response = client.post(
        f"/api/projects/{project['id']}/monitoring/run",
        json={"reference_dataset_id": ref["id"], "current_dataset_id": cur["id"]},
    )
    assert run_response.status_code == 201
    run = run_response.json()
    assert run["status"] == "completed"

    drift = client.get(f"/api/monitoring/{run['id']}/drift").json()
    assert len(drift) > 0
    age_results = [d for d in drift if d["feature_name"] == "age"]
    assert any(d["metric_name"] == "psi" for d in age_results)
