import io

from docx import Document


def make_docx_bytes(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_upload_resumes_parses_docx(client, make_user):
    _, headers = make_user()
    job = client.post(
        "/jobs", json={"title": "Backend Developer", "description": "Python"}, headers=headers
    ).json()

    files = [
        ("files", ("resume.docx", make_docx_bytes("Experienced Python developer"), "application/octet-stream"))
    ]
    res = client.post(f"/jobs/{job['id']}/resumes", files=files, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["created"]) == 1
    assert body["failed"] == []
    assert body["created"][0]["file_name"] == "resume.docx"


def test_upload_isolates_per_file_failures(client, make_user):
    _, headers = make_user()
    job = client.post(
        "/jobs", json={"title": "Backend Developer", "description": "Python"}, headers=headers
    ).json()

    files = [
        ("files", ("good.docx", make_docx_bytes("A valid resume"), "application/octet-stream")),
        ("files", ("bad.txt", b"not a supported format", "text/plain")),
    ]
    res = client.post(f"/jobs/{job['id']}/resumes", files=files, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["created"]) == 1
    assert body["created"][0]["file_name"] == "good.docx"
    assert len(body["failed"]) == 1
    assert body["failed"][0]["file_name"] == "bad.txt"
    assert "bad.txt" in body["failed"][0]["error"]  # no leaked temp filename


def test_upload_requires_an_existing_job_owned_by_the_caller(client, make_user):
    _, headers_a = make_user()
    _, headers_b = make_user()
    job = client.post("/jobs", json={"title": "A's job", "description": "d"}, headers=headers_a).json()

    files = [("files", ("resume.docx", make_docx_bytes("text"), "application/octet-stream"))]
    res = client.post(f"/jobs/{job['id']}/resumes", files=files, headers=headers_b)
    assert res.status_code == 404


def test_rank_requires_at_least_one_resume(client, make_user):
    _, headers = make_user()
    job = client.post("/jobs", json={"title": "Backend Developer", "description": "Python"}, headers=headers).json()

    res = client.post(f"/jobs/{job['id']}/rank", headers=headers)
    assert res.status_code == 400


def test_rank_orders_by_final_score_and_persists_results(client, make_user, monkeypatch):
    # Semantic scoring loads a real SBERT model, which is slow and makes CI
    # non-deterministic across torch/model versions. Mock it to isolate the
    # ranking/blend/persistence logic under test, not the ML model itself.
    import backend.app.main as main_module

    def fake_semantic_rank(job_text, resume_texts):
        # Return scores that deliberately disagree with keyword overlap, so
        # we're actually exercising the blend, not just one signal.
        return [0.9 if "strong" in t else 0.1 for t in resume_texts]

    monkeypatch.setattr(main_module, "semantic_rank", fake_semantic_rank)

    _, headers = make_user()
    job = client.post(
        "/jobs",
        json={"title": "Backend Developer", "description": "python fastapi postgresql"},
        headers=headers,
    ).json()

    files = [
        ("files", ("strong.docx", make_docx_bytes("strong match python fastapi postgresql"), "application/octet-stream")),
        ("files", ("weak.docx", make_docx_bytes("weak match marketing excel"), "application/octet-stream")),
    ]
    client.post(f"/jobs/{job['id']}/resumes", files=files, headers=headers)

    res = client.post(f"/jobs/{job['id']}/rank", headers=headers)
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 2
    assert results[0]["rank"] == 1
    assert results[0]["file_name"] == "strong.docx"
    assert results[0]["final_score"] > results[1]["final_score"]

    # Results should also be fetchable later without re-ranking.
    fetched = client.get(f"/jobs/{job['id']}/results", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json() == results


def test_candidate_detail_requires_ownership(client, make_user):
    _, headers_a = make_user()
    _, headers_b = make_user()
    job = client.post("/jobs", json={"title": "job", "description": "d"}, headers=headers_a).json()
    files = [("files", ("resume.docx", make_docx_bytes("text"), "application/octet-stream"))]
    created = client.post(f"/jobs/{job['id']}/resumes", files=files, headers=headers_a).json()["created"][0]

    res = client.get(f"/candidates/{created['id']}", headers=headers_b)
    assert res.status_code == 404

    res = client.get(f"/candidates/{created['id']}", headers=headers_a)
    assert res.status_code == 200
    assert res.json()["raw_text"].strip() == "text"
