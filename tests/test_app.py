from fastapi.testclient import TestClient
from src.app import app, activities
from urllib.parse import quote


client = TestClient(app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Basic sanity check for a known activity
    assert "Chess Club" in data


def test_signup_and_unregister_cycle():
    activity = "Chess Club"
    email = "tester+pytest@example.com"

    # Ensure test email is not present initially
    if email in activities[activity]["participants"]:
        activities[activity]["participants"].remove(email)

    # Sign up
    signup_resp = client.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
    assert signup_resp.status_code == 200
    assert email in activities[activity]["participants"]

    # Unregister
    unregister_resp = client.delete(f"/activities/{quote(activity)}/unregister?email={quote(email)}")
    assert unregister_resp.status_code == 200
    assert email not in activities[activity]["participants"]
from fastapi.testclient import TestClient
import pytest

from src.app import app, activities

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    # Make a shallow copy and restore after each test to avoid cross-test pollution
    original = {k: {**v, "participants": list(v.get("participants", []))} for k, v in activities.items()}
    yield
    activities.clear()
    activities.update(original)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_unsubscribe_flow():
    activity = "Chess Club"
    email = "test.user@example.com"

    # Ensure not already signed up
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]

    # Sign up
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert f"Signed up {email} for {activity}" in resp.json().get("message", "")

    # Now participant should be present
    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]

    # Unregister
    resp = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert resp.status_code == 200
    assert f"Unregistered {email} from {activity}" in resp.json().get("message", "")

    # Participant should be gone
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_signup_existing_returns_400():
    activity = "Programming Class"
    existing = activities[activity]["participants"][0]

    resp = client.post(f"/activities/{activity}/signup?email={existing}")
    assert resp.status_code == 400


def test_unsubscribe_nonexistent_activity():
    resp = client.delete("/activities/Nonexistent/unregister?email=nobody@example.com")
    assert resp.status_code == 404


def test_unsubscribe_non_member():
    activity = "Chess Club"
    resp = client.delete(f"/activities/{activity}/unregister?email=not-in-list@example.com")
    assert resp.status_code == 404
