def test_signup_creates_account_and_returns_token(client):
    res = client.post("/auth/signup", json={"email": "alice@example.com", "password": "testpass123"})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_signup_rejects_duplicate_email(client):
    client.post("/auth/signup", json={"email": "bob@example.com", "password": "testpass123"})
    res = client.post("/auth/signup", json={"email": "bob@example.com", "password": "testpass123"})
    assert res.status_code == 400


def test_signup_rejects_short_password(client):
    res = client.post("/auth/signup", json={"email": "short@example.com", "password": "short"})
    assert res.status_code == 422


def test_login_succeeds_with_correct_password(client):
    client.post("/auth/signup", json={"email": "carol@example.com", "password": "testpass123"})
    res = client.post("/auth/login", json={"email": "carol@example.com", "password": "testpass123"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_rejects_wrong_password(client):
    client.post("/auth/signup", json={"email": "dave@example.com", "password": "testpass123"})
    res = client.post("/auth/login", json={"email": "dave@example.com", "password": "wrongpass"})
    assert res.status_code == 401


def test_login_rejects_unknown_email(client):
    res = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever123"})
    assert res.status_code == 401


def test_me_requires_a_token(client):
    res = client.get("/auth/me")
    assert res.status_code == 401


def test_me_returns_the_authenticated_user(client, make_user):
    email, headers = make_user()
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == email


def test_login_is_rate_limited_after_ten_attempts_per_minute(client):
    client.post("/auth/signup", json={"email": "ratelimit@example.com", "password": "testpass123"})

    statuses = []
    for _ in range(12):
        res = client.post(
            "/auth/login", json={"email": "ratelimit@example.com", "password": "wrongpass"}
        )
        statuses.append(res.status_code)

    assert statuses[:10] == [401] * 10
    assert all(s == 429 for s in statuses[10:])
