from copy import deepcopy

from yarl import URL

parent_issue_url = URL("http://localhost:8080/rest/api/2/issue/10000")
parent_issue_transitions_url = URL("http://localhost:8080/rest/api/2/issue/10000/transitions")

issue_created = {
    "webhookEvent": "jira:issue_created",
    "issue": {
        "id": "10123",
        "key": "TPROJ-30",
        "fields": {"parent": {"self": "http://localhost:8080/rest/api/2/issue/10000"}},
    },
}

issue_updated = deepcopy(issue_created)
issue_updated["webhookEvent"] = "jira:issue_updated"

issue_deleted = deepcopy(issue_created)
issue_deleted["webhookEvent"] = "jira:issue_deleted"

non_subtask_issue_updated = deepcopy(issue_updated)
del non_subtask_issue_updated["issue"]["fields"]["parent"]

parent_issue = {
    "self": "http://localhost:8080/rest/api/2/issue/10000",
    "key": "TPROJ-1",
    "fields": {
        "subtasks": [{"id": "10123", "fields": {"status": {"statusCategory": {"name": "In Progress"}}}}],
        "status": {"name": "To Do"},
    },
}

parent_issue_transition_not_required = deepcopy(parent_issue)
parent_issue_transition_not_required["fields"]["status"]["name"] = "In Progress"

parent_issue_in_unknown_status = deepcopy(parent_issue)
parent_issue_in_unknown_status["fields"]["status"]["name"] = "In Testing"

ready_for_dev_transitions = {
    "transitions": [{"id": "11", "to": {"name": "In Progress"}}, {"id": "21", "to": {"name": "Done"}}]
}
in_progress_transitions = {"transitions": [{"id": "1", "to": {"name": "To Do"}}, {"id": "21", "to": {"name": "Done"}}]}
done_transitions = {"transitions": [{"id": "1", "to": {"name": "To Do"}}, {"id": "11", "to": {"name": "In Progress"}}]}
