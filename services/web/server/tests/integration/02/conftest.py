# pylint:disable=unused-variable
# pylint:disable=unused-argument
# pylint:disable=redefined-outer-name

import json
from pathlib import Path
from typing import AsyncIterator, Dict
from uuid import uuid4

import pytest
from models_library.projects import ProjectID
from pytest_simcore.helpers.utils_projects import NewProject


@pytest.fixture(scope="session")
def fake_workbench_payload(tests_data_dir: Path) -> Dict:
    file_path = tests_data_dir / "workbench_sleeper_payload.json"
    with file_path.open() as fp:
        return json.load(fp)


@pytest.fixture(scope="session")
def fake_project(fake_data_dir: Path, fake_workbench_payload: Dict) -> Dict:
    project: Dict = {}
    with (fake_data_dir / "fake-project.json").open() as fp:
        project = json.load(fp)
    project["workbench"] = fake_workbench_payload["workbench"]
    return project


@pytest.fixture
def project_id() -> ProjectID:
    return uuid4()


@pytest.fixture
async def user_project(
    client, fake_project: Dict, logged_user: Dict, project_id: ProjectID
) -> AsyncIterator[Dict]:
    fake_project["prjOwner"] = logged_user["name"]
    fake_project["uuid"] = f"{project_id}"

    async with NewProject(
        fake_project, client.app, user_id=logged_user["id"]
    ) as project:
        yield project
