# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable
from typing import AsyncIterable

import aiodocker
import pytest
from faker import Faker
from models_library.services import RunID
from simcore_service_dynamic_sidecar.core.docker_utils import get_volume_by_label
from simcore_service_dynamic_sidecar.core.errors import VolumeNotFoundError


@pytest.fixture(scope="session")
def volume_name() -> str:
    return "test_source_name"


@pytest.fixture
def run_id(faker: Faker) -> RunID:
    return faker.uuid4(cast_to=None)


@pytest.fixture
async def volume_with_label(volume_name: str, run_id: RunID) -> AsyncIterable[None]:
    async with aiodocker.Docker() as docker_client:
        volume = await docker_client.volumes.create(
            {
                "Name": "test_volume_name_1",
                "Labels": {
                    "source": volume_name,
                    "run_id": f"{run_id}",
                },
            }
        )

        yield

        await volume.delete()


async def test_volume_with_label(
    volume_with_label: None, volume_name: str, run_id: RunID
) -> None:
    assert await get_volume_by_label(volume_name, run_id)


async def test_volume_label_missing(run_id: RunID) -> None:
    with pytest.raises(VolumeNotFoundError) as exc_info:
        await get_volume_by_label("not_exist", run_id)

    error_msg = f"{exc_info.value}"
    assert f"{run_id}" in error_msg
    assert "not_exist" in error_msg
