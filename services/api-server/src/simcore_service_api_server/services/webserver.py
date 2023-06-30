import json
import logging
import urllib.parse
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from cryptography import fernet
from fastapi import FastAPI, HTTPException
from httpx import Response
from models_library.api_schemas_webserver.projects import ProjectCreateNew, ProjectGet
from models_library.projects import ProjectID
from models_library.rest_pagination import Page
from models_library.utils.fastapi_encoders import jsonable_encoder
from pydantic import ValidationError
from servicelib.aiohttp.long_running_tasks.server import TaskStatus
from servicelib.error_codes import create_error_code
from starlette import status
from tenacity import TryAgain
from tenacity._asyncio import AsyncRetrying
from tenacity.before_sleep import before_sleep_log
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed

from ..core.settings import WebServerSettings
from ..models.pagination import MAXIMUM_NUMBER_OF_ITEMS_PER_PAGE
from ..models.types import JSON
from ..utils.client_base import BaseServiceClientApi, setup_client_instance

_logger = logging.getLogger(__name__)


@contextmanager
def _handle_webserver_api_errors():
    try:
        yield

    except ValidationError as exc:
        # Invalid formatted response body
        error_code = create_error_code(exc)
        _logger.exception(
            "Invalid data exchanged with webserver service [%s]",
            error_code,
            extra={"error_code": error_code},
        )
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail=error_code
        ) from exc

    except httpx.RequestError as exc:
        # e.g. TransportError, DecodingError, TooManyRedirects
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE) from exc

    except httpx.HTTPStatusError as exc:

        resp = exc.response
        if resp.is_server_error:
            _logger.exception(
                "webserver reponded with an error: %s [%s]",
                f"{resp.status_code=}",
                f"{resp.reason_phrase=}",
            )
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE) from exc

        if resp.is_client_error:
            # NOTE: Raise ProjectErrors / WebserverError that should be transformed into HTTP errors on the handler level
            error = exc.response.json().get("error", {})
            msg = error.get("errors") or resp.reason_phrase or f"{exc}"
            raise HTTPException(resp.status_code, detail=msg) from exc


class WebserverApi(BaseServiceClientApi):
    """Access to web-server API

    - BaseServiceClientApi:
        - wraps a httpx client
        - lifetime attached to app
        - responsive tests (i.e. ping) to API in-place

    """


@dataclass
class AuthSession:
    """
    - wrapper around thin-client to simplify webserver's API
    - sets endspoint upon construction
    - MIME type: application/json
    - processes responses, returning data or raising formatted HTTP exception
    - The lifetime of an AuthSession is ONE request.

    SEE services/api-server/src/simcore_service_api_server/api/dependencies/webserver.py
    """

    _api: WebserverApi
    vtag: str
    session_cookies: dict | None = None

    @classmethod
    def create(cls, app: FastAPI, session_cookies: dict) -> "AuthSession":
        api = WebserverApi.get_instance(app)
        assert api  # nosec
        assert isinstance(api, WebserverApi)  # nosec
        return cls(
            _api=api,
            vtag=app.state.settings.API_SERVER_WEBSERVER.WEBSERVER_VTAG,
            session_cookies=session_cookies,
        )

    @classmethod
    def _get_data_or_raise_http_exception(cls, resp: Response) -> JSON | None:
        # enveloped answer
        data: JSON | None = None
        error: JSON | None = None

        if resp.status_code != status.HTTP_204_NO_CONTENT:
            try:
                body = resp.json()
                data, error = body.get("data"), body.get("error")
            except json.JSONDecodeError:
                _logger.warning(
                    "Failed to unenvelop webserver response %s",
                    f"{resp.text=}",
                    exc_info=True,
                )

        if resp.is_server_error:
            _logger.error(
                "webserver reponded with an error: %s [%s]: %s",
                f"{resp.status_code=}",
                f"{resp.reason_phrase=}",
                error,
            )
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE)

        if resp.is_client_error:
            # NOTE: error is can be a dict
            msg = error or resp.reason_phrase
            raise HTTPException(resp.status_code, detail=msg)

        return data

    # OPERATIONS

    @property
    def client(self):
        return self._api.client

    async def get(self, path: str) -> JSON | None:
        url = path.lstrip("/")
        try:
            resp = await self.client.get(url, cookies=self.session_cookies)
        except Exception as err:
            _logger.exception("Failed to get %s", url)
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE) from err

        return self._get_data_or_raise_http_exception(resp)

    async def put(self, path: str, body: dict) -> JSON | None:
        url = path.lstrip("/")
        try:
            resp = await self.client.put(url, json=body, cookies=self.session_cookies)
        except Exception as err:
            _logger.exception("Failed to put %s", url)
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE) from err

        return self._get_data_or_raise_http_exception(resp)

    # PROJECTS resource ---

    async def create_project(self, project: ProjectCreateNew) -> ProjectGet:
        # POST /projects --> 202
        resp = await self.client.post(
            "/projects",
            params={"hidden": True},
            json=jsonable_encoder(project, by_alias=True, exclude={"state"}),
            cookies=self.session_cookies,
        )
        data: JSON | None = self._get_data_or_raise_http_exception(resp)
        assert data  # nosec
        assert isinstance(data, dict)  # nosec

        # NOTE: /v0 is already included in the http client base_url
        status_url = data["status_href"].lstrip(f"/{self.vtag}")
        result_url = data["result_href"].lstrip(f"/{self.vtag}")
        # GET task status now until done
        async for attempt in AsyncRetrying(
            wait=wait_fixed(0.5),
            stop=stop_after_delay(60),
            reraise=True,
            before_sleep=before_sleep_log(_logger, logging.INFO),
        ):
            with attempt:
                data = await self.get(status_url)
                task_status = TaskStatus.parse_obj(data)
                if not task_status.done:
                    msg = "Timed out creating project. TIP: Try again, or contact oSparc support if this is happening repeatedly"
                    raise TryAgain(msg)

        data = await self.get(f"{result_url}")
        return ProjectGet.parse_obj(data)

    async def get_project(self, project_id: UUID) -> ProjectGet:
        resp = await self.client.get(
            f"/projects/{project_id}",
            cookies=self.session_cookies,
        )

        data: JSON | None = self._get_data_or_raise_http_exception(resp)
        return ProjectGet.parse_obj(data)

    async def list_projects(
        self, solver_name: str, limit: int, offset: int
    ) -> Page[ProjectGet]:
        assert 1 <= limit <= MAXIMUM_NUMBER_OF_ITEMS_PER_PAGE  # nosec
        assert offset >= 0  # nosec
        with _handle_webserver_api_errors():
            resp = await self.client.get(
                "/projects",
                params={
                    "type": "user",
                    "show_hidden": True,
                    "limit": limit,
                    "offset": offset,
                    # WARNING: better way to match jobs with projects (Next PR if this works fine!)
                    "search": urllib.parse.quote(solver_name, safe=""),
                    # WARNING: search text has a limit that I needed to increas for the example!
                },
                cookies=self.session_cookies,
            )
            resp.raise_for_status()

            return Page[ProjectGet].parse_raw(resp.text)

    async def delete_project(self, project_id: ProjectID) -> None:
        resp = await self.client.delete(
            f"/projects/{project_id}", cookies=self.session_cookies
        )
        self._get_data_or_raise_http_exception(resp)

    async def get_project_metadata_ports(
        self, project_id: ProjectID
    ) -> list[dict[str, Any]]:
        """
        maps GET "/projects/{study_id}/metadata/ports", unenvelopes
        and returns data
        """
        resp = await self.client.get(
            f"/projects/{project_id}/metadata/ports",
            cookies=self.session_cookies,
        )
        data = self._get_data_or_raise_http_exception(resp)
        assert data
        assert isinstance(data, list)
        return data


# MODULES APP SETUP -------------------------------------------------------------


def setup(app: FastAPI, settings: WebServerSettings | None = None) -> None:
    if not settings:
        settings = WebServerSettings.create_from_envs()

    assert settings is not None  # nosec

    setup_client_instance(
        app, WebserverApi, api_baseurl=settings.api_base_url, service_name="webserver"
    )

    def _on_startup() -> None:
        # normalize & encrypt
        secret_key = settings.WEBSERVER_SESSION_SECRET_KEY.get_secret_value()
        app.state.webserver_fernet = fernet.Fernet(secret_key)

    async def _on_shutdown() -> None:
        _logger.debug("Webserver closed successfully")

    app.add_event_handler("startup", _on_startup)
    app.add_event_handler("shutdown", _on_shutdown)