# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

import random
from typing import AsyncIterable, AsyncIterator

import pytest
import traitlets.config
from _dask_helpers import DaskGatewayServer
from _pytest.monkeypatch import MonkeyPatch
from dask.distributed import Scheduler, Worker
from dask_gateway_server.app import DaskGateway
from dask_gateway_server.backends.inprocess import InProcessBackend
from distributed.deploy.spec import SpecCluster
from models_library.service_settings_labels import SimcoreServiceLabels
from pydantic.types import NonNegativeInt
from simcore_service_director_v2.models.domains.dynamic_services import (
    DynamicServiceCreate,
)
from simcore_service_director_v2.models.schemas.dynamic_services import (
    SchedulerData,
    ServiceDetails,
    ServiceLabelsStoredData,
)
from yarl import URL


@pytest.fixture
def simcore_services_network_name() -> str:
    return "test_network_name"


@pytest.fixture(autouse=True)
def disable_dynamic_sidecar_scheduler_in_unit_tests(
    monkeypatch, simcore_services_network_name: str
) -> None:
    # FIXME: PC-> ANE: please avoid autouse!!!
    monkeypatch.setenv("REGISTRY_AUTH", "false")
    monkeypatch.setenv("REGISTRY_USER", "test")
    monkeypatch.setenv("REGISTRY_PW", "test")
    monkeypatch.setenv("REGISTRY_SSL", "false")
    monkeypatch.setenv("SIMCORE_SERVICES_NETWORK_NAME", simcore_services_network_name)
    monkeypatch.setenv("TRAEFIK_SIMCORE_ZONE", "test_traefik_zone")
    monkeypatch.setenv("SWARM_STACK_NAME", "test_swarm_name")


@pytest.fixture
def simcore_service_labels() -> SimcoreServiceLabels:
    return SimcoreServiceLabels(
        **SimcoreServiceLabels.Config.schema_extra["examples"][1]
    )


@pytest.fixture
def dynamic_service_create() -> DynamicServiceCreate:
    return DynamicServiceCreate.parse_obj(ServiceDetails.Config.schema_extra["example"])


@pytest.fixture
def service_labels_stored_data() -> ServiceLabelsStoredData:
    return ServiceLabelsStoredData.parse_obj(
        ServiceLabelsStoredData.Config.schema_extra["example"]
    )


@pytest.fixture(scope="session")
def dynamic_sidecar_port() -> int:
    return 1222


@pytest.fixture
def scheduler_data_from_http_request(
    dynamic_service_create: DynamicServiceCreate,
    simcore_service_labels: SimcoreServiceLabels,
    dynamic_sidecar_port: int,
) -> SchedulerData:
    return SchedulerData.from_http_request(
        service=dynamic_service_create,
        simcore_service_labels=simcore_service_labels,
        port=dynamic_sidecar_port,
    )


@pytest.fixture
def scheduler_data_from_service_labels_stored_data(
    service_labels_stored_data: ServiceLabelsStoredData, dynamic_sidecar_port: int
) -> SchedulerData:
    return SchedulerData.from_service_labels_stored_data(
        service_labels_stored_data=service_labels_stored_data, port=dynamic_sidecar_port
    )


@pytest.fixture
def cluster_id() -> NonNegativeInt:
    return random.randint(0, 10)


@pytest.fixture
def cluster_id_resource_name(cluster_id: NonNegativeInt) -> str:
    return f"CLUSTER_{cluster_id}"


@pytest.fixture
async def dask_spec_local_cluster(
    monkeypatch: MonkeyPatch,
    cluster_id_resource_name: str,
) -> AsyncIterable[SpecCluster]:
    # in this mode we can precisely create a specific cluster
    workers = {
        "cpu-worker": {
            "cls": Worker,
            "options": {
                "nthreads": 2,
                "resources": {"CPU": 2, "RAM": 48e9, cluster_id_resource_name: 1},
            },
        },
        "gpu-worker": {
            "cls": Worker,
            "options": {
                "nthreads": 1,
                "resources": {
                    "CPU": 1,
                    "GPU": 1,
                    "RAM": 48e9,
                    cluster_id_resource_name: 1,
                },
            },
        },
        "mpi-worker": {
            "cls": Worker,
            "options": {
                "nthreads": 1,
                "resources": {
                    "CPU": 8,
                    "MPI": 1,
                    "RAM": 768e9,
                    cluster_id_resource_name: 1,
                },
            },
        },
        "gpu-mpi-worker": {
            "cls": Worker,
            "options": {
                "nthreads": 1,
                "resources": {
                    "GPU": 1,
                    "MPI": 1,
                    "RAM": 768e9,
                    cluster_id_resource_name: 1,
                },
            },
        },
    }
    scheduler = {"cls": Scheduler, "options": {"dashboard_address": ":8787"}}

    async with SpecCluster(
        workers=workers, scheduler=scheduler, asynchronous=True
    ) as cluster:
        scheduler_address = URL(cluster.scheduler_address)
        monkeypatch.setenv("DASK_SCHEDULER_HOST", scheduler_address.host or "invalid")
        monkeypatch.setenv("DASK_SCHEDULER_PORT", f"{scheduler_address.port}")
        yield cluster


@pytest.fixture
async def local_dask_gateway_server() -> AsyncIterator[DaskGatewayServer]:
    c = traitlets.config.Config()
    c.DaskGateway.backend_class = InProcessBackend  # type: ignore
    c.DaskGateway.address = "127.0.0.1:0"  # type: ignore
    c.Proxy.address = "127.0.0.1:0"  # type: ignore
    c.DaskGateway.authenticator_class = "dask_gateway_server.auth.SimpleAuthenticator"  # type: ignore
    c.SimpleAuthenticator.password = "qweqwe"  # type: ignore
    print("--> creating local dask gateway server")
    dask_gateway_server = DaskGateway(config=c)
    dask_gateway_server.initialize([])  # that is a shitty one!
    print("--> local dask gateway server initialized")
    await dask_gateway_server.setup()
    await dask_gateway_server.backend.proxy._proxy_contacted  # pylint: disable=protected-access
    print("--> local dask gateway server setup completed")
    yield DaskGatewayServer(
        f"http://{dask_gateway_server.backend.proxy.address}",
        f"gateway://{dask_gateway_server.backend.proxy.tcp_address}",
        c.SimpleAuthenticator.password,  # type: ignore
    )
    print("--> local dask gateway server switching off...")
    await dask_gateway_server.cleanup()
    print("...done")
