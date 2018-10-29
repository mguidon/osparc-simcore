# pylint:disable=unused-import
# pylint:disable=unused-argument
# pylint:disable=redefined-outer-name

import pytest
from aiohttp import web

from utils_login import LoggedUser
from utils_assert import assert_status
from servicelib.response_utils import unwrap_envelope
from servicelib.rest_utils import extract_and_validate


# from simcore_service_webserver.application_keys import APP_CONFIG_KEY
# from simcore_service_webserver.storage import setup_storage
# from simcore_service_webserver.rest import setup_rest


# TODO: create a fake storage service here
@pytest.fixture(scope="module")
def storage_server(loop, aiohttp_server, app_cfg):
    cfg = app_cfg["storage"]
    
    app = web.Application()
    def _get_locs(request: web.Request):
        params, query, body = await extract_and_validate(request)
        
        assert params is None, params
        assert query, query
        assert body, body

        assert query["user_id"], "Expected user id"
        return web.json_response({
            'data': [query, ]
        })

    app.router.add_get("/v0/storage/locations/", _get_locs)
    assert cfg['host']=='localhost'

    server = loop.run_until_complete(aiohttp_server(app, port= cfg['port']))
    return server

@pytest.mark.travis
async def test_storage_locations(client, storage_server):
    url = "/v0/storage/locations"

    resp = await client.get(url)
    await assert_status(resp, web.HTTPUnauthorized)

    async with LoggedUser(client) as user:
        print("Logged user:", user) # TODO: can use in the test

        resp = await client.get(url)

        payload = await resp.json()
        assert resp.status == 200, str(payload)

        data, error = unwrap_envelope(payload)

        assert len(data) == 1
        assert not error

        assert data[0]['user_id'] == user['user_id']

