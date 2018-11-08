#pylint: disable=W0621, unused-argument
import logging
import threading

import pytest
import requests
from pytest_docker import docker_ip, docker_services  # pylint:disable=W0611

from simcore_service_storage_sdk import ApiClient, Configuration, UsersApi

log = logging.getLogger(__name__)

def _fake_logger_while_building_storage():
    print("Hey Travis I'm still alive...")

def _is_responsive(url, code=200):
    try:
        if requests.get(url).status_code == code:
            return True
    except Exception:  #pylint: disable=W0703
        logging.exception("Connection to storage failed")
        return False

    return False

@pytest.fixture(scope="module")
def storage(bucket, engine, docker_ip, docker_services): 
    host = docker_ip
    port = docker_services.port_for('storage', 8080)
    endpoint = "http://{}:{}".format(host, port)
    # Wait until we can connect
    keep_alive_timer = threading.Timer(interval=60.0, function=_fake_logger_while_building_storage)
    keep_alive_timer.start()
    docker_services.wait_until_responsive(
        check=lambda: _is_responsive(endpoint, 404),
        timeout=20.0*60.0,
        pause=1.0,
    )
    keep_alive_timer.cancel()
    
    yield endpoint
    # cleanup
    
@pytest.fixture()    
async def storage_api(storage):
    config = Configuration()
    config.host = "{}/{}".format(storage, "v0")
    client = ApiClient(config)
    api = UsersApi(client)
    yield api
    
