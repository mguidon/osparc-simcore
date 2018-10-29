import aiohttp
from aiohttp import web
from yarl import URL

from servicelib.request_keys import RQT_USERID_KEY
from servicelib.rest_utils import extract_and_validate

from .db_models import UserRole
from .login.decorators import login_required, restricted_to
from .storage_settings import get_config

# TODO: retrieve from db tokens



async def _storage_get(request: web.Request, url_path: str):
    # TODO: Implement redirects with client sdk or aiohttp client

    await extract_and_validate(request)

    cfg = get_config(request.app)
    urlbase = URL.build(scheme='http', host=cfg['host'], port=cfg['port'])

    userid = request[RQT_USERID_KEY]
    url = urlbase.with_path(url_path).with_query(user_id=userid)

    async with aiohttp.ClientSession() as session: # TODO: check if should keep webserver->storage session? 
        async with session.get(url, ssl=False) as resp:
            payload = await resp.json()
            return payload


@login_required
async def get_storage_locations(request: web.Request):
    await extract_and_validate(request)

    locs = [{"name": "bla", "id": 0}]

    envelope = {
        'error': None,
        'data': locs
    }

    return envelope

@login_required
async def get_files_metadata(request: web.Request):
    _params, _query, _body = await extract_and_validate(request)
    # get user_id, add to query and pass to storage
    raise NotImplementedError


@login_required
async def get_file_metadata(request: web.Request):
    _params, _query, _body = await extract_and_validate(request)

    # get user_id, add to query and pass to storage
    raise NotImplementedError


@login_required
async def update_file_meta_data(request: web.Request):
    _params, _query, _body = await extract_and_validate(request)

    # get user_id, add to query and pass to storage
    raise NotImplementedError


@login_required
async def download_file(request: web.Request):
    _params, _query, _body = await extract_and_validate(request)

    # get user_id, add to query and pass to storage
    raise NotImplementedError


@login_required
async def upload_file(request: web.Request):
    _params, _query, _body = await extract_and_validate(request)

    # get user_id, add to query and pass to storage
    raise NotImplementedError


@restricted_to(UserRole.MODERATOR)
async def delete_file(request: web.Request):
    _params, _query, _body = await extract_and_validate(request)

    # get user_id, add to query and pass to storage
    raise NotImplementedError
