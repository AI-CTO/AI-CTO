import json
import os
import sys
from urllib import response

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

mock_businessPlan = os.path.join(os.path.dirname(__file__), "mockBusinessPlan.txt")
with open(mock_businessPlan, "r") as file:
    business_plan = file.read()

idea_pdf = os.path.join(os.path.dirname(__file__), "idea.pdf")


project_id = None
thread_id = None


def test_home(client):
    response = client.get("/")
    assert b"<title>AI Project Tool</title>" in response.data


def test_create_and_get_project(client):
    global project_id
    global thread_id

    response = client.post("/process_project", json={"description": business_plan})
    assert response.status_code == 200

    response_data = response.get_json()
    assert "thread_id" in response_data
    assert "assistant_response" in response_data

    thread_id = response_data["thread_id"]

    response = client.get("/get_projects")
    assert response.status_code == 200

    response_data = response.get_json()
    projects = response_data.get("projects", [])

    for project in projects:
        if project["thread_id"] == thread_id:
            project_id = project["id"]
            break

    assert project_id is not None, "Project ID was not found in the list of projects."

def test_upload_pdf(client):
    global project_id
    global thread_id

    response = client.post("/upload_pdf", json={"description": idea_pdf})
    assert response.status_code == 200

    response_data = response.get_json()
    assert "thread_id" in response_data
    assert "assistant_response" in response_data

    thread_id = response_data["thread_id"]

    response = client.get("/get_projects")
    assert response.status_code == 200

    response_data = response.get_json()
    projects = response_data.get("projects", [])

    for project in projects:
        if project["thread_id"] == thread_id:
            project_id = project["id"]
            break

    assert project_id is not None, "Project ID was not found in the list of projects."

def test_evaluate_project(client):
    global project_id
    assert project_id is not None, "No valid project_id found from previous test."

    response = client.post(f"/evaluate_project", json={"thread_id": thread_id})
    assert response.status_code == 200

    response_data = response.get_json()
    assert "evaluation" in response_data


def test_update_project(client):
    global project_id
    assert project_id is not None, "No valid project_id found from previous tests."

    response = client.get(f"/update_project?id={project_id}")

    assert response.status_code == 200, f"Failed to fetch project: {response.get_json()}"

def test_cleanup_project(client):
    global project_id
    assert project_id is not None, "No valid project_id found from previous tests."

    response = client.delete(f"/delete_project/{project_id}")
    assert response.status_code == 200

    response_data = response.get_json()
    assert response_data.get("message") == "Project deleted!"

    response = client.get("/get_projects")
    response_data = response.get_json()
    projects = response_data.get("projects", [])

    assert not any(p["id"] == project_id for p in projects), "Project was not deleted."
