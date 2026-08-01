import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: snapshot the original in-memory activity store before each test.
    original_state = copy.deepcopy(app_module.activities)

    # Act: restore the state before the test runs.
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_state))
    yield

    # Assert: restore the state after the test finishes.
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_state))


@pytest.fixture()
def client():
    # Create a test client to exercise the FastAPI app without launching a server.
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_unregister_participant_removes_email(client):
    # Arrange: define the activity and participant that will be removed.
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act: send the unregister request to the API.
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert: verify the API returns a success response and the expected message.
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"

    # Assert: confirm the participant is no longer present in the activity data.
    activities = client.get("/activities").json()
    assert email not in activities[activity_name]["participants"]


def test_signup_participant_adds_email_to_activity(client):
    # Arrange: define a new activity signup.
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act: send the signup request to the API.
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: verify the API accepts the signup and returns a success message.
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"

    # Assert: confirm the participant appears in the activity data.
    activities = client.get("/activities").json()
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange: define a participant that is already registered.
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act: try to sign up the same participant again.
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert: verify the API rejects the duplicate signup.
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
