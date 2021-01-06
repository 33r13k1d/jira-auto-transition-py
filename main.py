from typing import Optional

import aiohttp
from fastapi import FastAPI, Body, Depends

from pydantic import BaseSettings


class Settings(BaseSettings):
    JIRA_ACCESS_TOKEN: str

    PARENT_READY_FOR_DEV_STATUS_NAME: str = "To Do"
    PARENT_IN_PROGRESS_STATUS_NAME: str = "In Progress"
    PARENT_DONE_STATUS_NAME: str = "Done"

    class Config:
        env_file = ".env"


settings = Settings()
app = FastAPI()


class HttpClient:
    session: Optional[aiohttp.ClientSession] = None

    @classmethod
    def start(cls, headers):
        cls.session = aiohttp.ClientSession(headers=headers)

    @classmethod
    async def stop(cls):
        await cls.session.close()
        cls.session = None

    def __call__(self) -> aiohttp.ClientSession:
        assert self.session is not None
        return self.session


jira_client = HttpClient()


@app.on_event("startup")
async def startup():
    headers = {"Authorization": f"Bearer {settings.JIRA_ACCESS_TOKEN}"}
    jira_client.start(headers)


@app.on_event("shutdown")
async def shutdown_event():
    await jira_client.stop()


TARGET_STATUSES_MAP = {
    ("In Progress",): settings.PARENT_IN_PROGRESS_STATUS_NAME,
    ("Done",): settings.PARENT_DONE_STATUS_NAME,
    ("To Do",): settings.PARENT_READY_FOR_DEV_STATUS_NAME,
    (): settings.PARENT_READY_FOR_DEV_STATUS_NAME,
}


@app.post("/hook")
async def handle_jira_subtask_transition(body: dict = Body(...), client: aiohttp.ClientSession = Depends(jira_client)):

    parent: dict = body["issue"]["fields"].get("parent")
    if not parent:
        print("Not a subtask issue type. Check your webhook configuration.")
        return

    async with client.get(parent["self"]) as r:
        r.raise_for_status()
        parent_issue: dict = await r.json()

    parent_subtasks: list = parent_issue["fields"]["subtasks"]

    if body["webhookEvent"] == "jira:issue_deleted":
        parent_subtasks = [p for p in parent_subtasks if p["id"] != body["issue"]["id"]]

    status_class_names = {s["fields"]["status"]["statusCategory"]["name"] for s in parent_subtasks}

    target_status_name: str = TARGET_STATUSES_MAP.get(tuple(status_class_names), "In Progress")

    await do_transition_if_needed(client, parent_issue, target_status_name)


async def do_transition_if_needed(client: aiohttp.ClientSession, issue: dict, target_status_name: str):
    current_status_name = issue["fields"]["status"]["name"]

    if current_status_name == target_status_name or current_status_name not in set(TARGET_STATUSES_MAP.values()):
        print("Transition is not needed")
        return

    async with client.get(issue["self"] + "/transitions") as r:
        r.raise_for_status()
        parent_transitions: dict = (await r.json())["transitions"]

    transition = next((t for t in parent_transitions if t["to"]["name"] == target_status_name), None)

    if not transition:
        print(f'Transition from "{issue["fields"]["status"]["name"]}" to "{target_status_name}" not found')
        return

    payload = {"transition": {"id": transition["id"]}}
    async with client.post(issue["self"] + "/transitions", json=payload) as r:
        r.raise_for_status()
