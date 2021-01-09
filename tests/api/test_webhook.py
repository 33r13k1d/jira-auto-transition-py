from copy import deepcopy
from random import randint

from fastapi.testclient import TestClient
from aioresponses import aioresponses
from requests import Response
import pytest

from .data import test_data as td


@pytest.mark.parametrize(
    "task_status, subtask_statuses, task_transitions, final_task_status",
    [
        ("To Do", ["In Progress"], td.ready_for_dev_transitions, "In Progress"),
        ("To Do", ["Done"], td.ready_for_dev_transitions, "Done"),
        ("Done", ["To Do"], td.done_transitions, "To Do"),
        ("Done", ["In Progress"], td.done_transitions, "In Progress"),
        ("In Progress", ["To Do"], td.in_progress_transitions, "To Do"),
        ("In Progress", ["Done"], td.in_progress_transitions, "Done"),
        ("In Progress", ["Done", "Done"], td.in_progress_transitions, "Done"),
        ("To Do", ["In Progress", "In Progress"], td.ready_for_dev_transitions, "In Progress"),
        ("Done", ["Done", "In Progress"], td.done_transitions, "In Progress"),
        ("Done", ["Done", "To Do"], td.done_transitions, "In Progress"),
        ("Done", [], td.done_transitions, "To Do"),
    ],
)
def test_single_subtask_transitions(
    aioresps: aioresponses,
    client: TestClient,
    task_status: str,
    subtask_statuses: list,
    task_transitions: dict,
    final_task_status: str,
) -> None:
    parent_issue = deepcopy(td.parent_issue)
    parent_issue["fields"]["status"]["name"] = task_status
    parent_issue["fields"]["subtasks"] = [
        {"id": f"{randint(10, 10000)}", "fields": {"status": {"statusCategory": {"name": sn}}}}
        for sn in subtask_statuses
    ]

    aioresps.get(td.parent_issue_url, payload=parent_issue)
    aioresps.get(td.parent_issue_transitions_url, payload=task_transitions)
    aioresps.post(td.parent_issue_transitions_url)

    r: Response = client.post(f"sub-task-event", json=td.issue_updated if subtask_statuses else td.issue_deleted)

    assert r.status_code == 200
    assert len(aioresps.requests) == 3

    transition_id = next(t["id"] for t in task_transitions["transitions"] if t["to"]["name"] == final_task_status)
    assert aioresps.requests[("POST", td.parent_issue_transitions_url)][0].kwargs["json"] == {
        "transition": {"id": f"{transition_id}"}
    }


def test_transition_not_found(aioresps: aioresponses, client: TestClient) -> None:
    aioresps.get(td.parent_issue_url, payload=td.parent_issue)
    aioresps.get(td.parent_issue_transitions_url, payload=td.in_progress_transitions)

    r: Response = client.post(f"sub-task-event", json=td.issue_updated)

    assert r.status_code == 200
    assert len(aioresps.requests) == 2
    assert not aioresps.requests.get(("POST", td.parent_issue_transitions_url))


def test_jira_deletion_lag(aioresps: aioresponses, client: TestClient) -> None:
    aioresps.get(td.parent_issue_url, payload=td.parent_issue_transition_not_required)
    aioresps.get(td.parent_issue_transitions_url, payload=td.in_progress_transitions)
    aioresps.post(td.parent_issue_transitions_url)

    r: Response = client.post(f"sub-task-event", json=td.issue_deleted)

    assert r.status_code == 200
    assert len(aioresps.requests) == 3
    assert aioresps.requests[("POST", td.parent_issue_transitions_url)][0].kwargs["json"] == {"transition": {"id": "1"}}


def test_skip_transition_to_current_status(aioresps: aioresponses, client: TestClient) -> None:
    aioresps.get(td.parent_issue_url, payload=td.parent_issue_transition_not_required)

    r: Response = client.post(f"sub-task-event", json=td.issue_created)

    assert r.status_code == 200
    assert len(aioresps.requests) == 1
    assert not aioresps.requests.get(("POST", td.parent_issue_transitions_url))


def test_skip_transition_from_unknown_status(aioresps: aioresponses, client: TestClient) -> None:
    aioresps.get(td.parent_issue_url, payload=td.parent_issue_in_unknown_status)

    r: Response = client.post(f"sub-task-event", json=td.issue_created)

    assert r.status_code == 200
    assert len(aioresps.requests) == 1
    assert not aioresps.requests.get(("POST", td.parent_issue_transitions_url))


def test_event_from_non_subtask_issue(aioresps: aioresponses, client: TestClient) -> None:
    r: Response = client.post(f"sub-task-event", json=td.non_subtask_issue_updated)

    assert r.status_code == 200
    assert not aioresps.requests
