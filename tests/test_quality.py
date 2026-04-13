from __future__ import annotations


def test_invalid_schedule_key_returns_422(client):
    r = client.post(
        "/auth/register-doctor",
        json={
            "name": "Dr",
            "email": "badsched@example.com",
            "address": "Sofia",
            "password": "secret12",
            "schedule": {"not_a_day": []},
        },
    )
    assert r.status_code == 422


def test_missing_bearer_returns_401(client):
    r = client.get("/appointments/me")
    assert r.status_code == 401


def test_invalid_jwt_returns_401(client):
    r = client.get("/appointments/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_overlapping_schedule_intervals_returns_422(client):
    r = client.post(
        "/auth/register-doctor",
        json={
            "name": "Dr",
            "email": "overlap@example.com",
            "address": "Sofia",
            "password": "secret12",
            "schedule": {"monday": [["08:00", "10:00"], ["09:00", "11:00"]]},
        },
    )
    assert r.status_code == 422
