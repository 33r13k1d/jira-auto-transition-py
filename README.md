# jira-auto-transition-py

Automatically change parent issue status according to children's statuses.

Configuration options (env vars):
```
JIRA_AUTH_HEADER: str
JIRA_BASE_URL: Optional[str] = None

PARENT_READY_FOR_DEV_STATUS_NAME: str = "To Do"
PARENT_IN_PROGRESS_STATUS_NAME: str = "In Progress"
PARENT_DONE_STATUS_NAME: str = "Done"

LOG_LEVEL: str = "INFO"

RELAXED_SSL: bool = False
```

`.env` file can be used for configuration.
