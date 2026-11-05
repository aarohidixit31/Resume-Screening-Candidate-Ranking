def test_create_and_list_job(client, make_user):
    _, headers = make_user()
    res = client.post(
        "/jobs", json={"title": "Backend Developer", "description": "Python, FastAPI"}, headers=headers
    )
    assert res.status_code == 200
    job = res.json()
    assert job["title"] == "Backend Developer"

    res = client.get("/jobs", headers=headers)
    assert res.status_code == 200
    assert any(j["id"] == job["id"] for j in res.json())


def test_jobs_are_scoped_to_their_owner(client, make_user):
    _, headers_a = make_user()
    _, headers_b = make_user()

    client.post("/jobs", json={"title": "Job A", "description": "desc"}, headers=headers_a)

    res = client.get("/jobs", headers=headers_b)
    assert res.status_code == 200
    assert res.json() == []


def test_create_job_requires_auth(client):
    res = client.post("/jobs", json={"title": "x", "description": "y"})
    assert res.status_code == 401


def test_patch_updates_job_fields(client, make_user):
    _, headers = make_user()
    job = client.post(
        "/jobs", json={"title": "Old Title", "description": "Old desc"}, headers=headers
    ).json()

    res = client.patch(f"/jobs/{job['id']}", json={"title": "New Title"}, headers=headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["title"] == "New Title"
    assert updated["description"] == "Old desc"


def test_cannot_patch_another_users_job(client, make_user):
    _, headers_a = make_user()
    _, headers_b = make_user()
    job = client.post("/jobs", json={"title": "A's job", "description": "desc"}, headers=headers_a).json()

    res = client.patch(f"/jobs/{job['id']}", json={"title": "Hijacked"}, headers=headers_b)
    assert res.status_code == 404


def test_delete_job_removes_it(client, make_user):
    _, headers = make_user()
    job = client.post("/jobs", json={"title": "Temp", "description": "desc"}, headers=headers).json()

    res = client.delete(f"/jobs/{job['id']}", headers=headers)
    assert res.status_code == 204

    res = client.get(f"/jobs/{job['id']}/results", headers=headers)
    assert res.status_code == 404


def test_delete_nonexistent_job_returns_404_not_500(client, make_user):
    _, headers = make_user()
    res = client.delete("/jobs/999999", headers=headers)
    assert res.status_code == 404


def test_job_title_too_long_is_rejected(client, make_user):
    _, headers = make_user()
    res = client.post(
        "/jobs", json={"title": "x" * 300, "description": "desc"}, headers=headers
    )
    assert res.status_code == 422
