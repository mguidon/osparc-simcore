""" Utils to implement READ operations (from cRud) on the project resource


Read operations are list, get

"""

from aiohttp import web
from models_library.api_schemas_webserver._base import OutputSchema
from models_library.api_schemas_webserver.projects import ProjectListItem
from models_library.folders import FolderID
from models_library.projects import ProjectID
from models_library.rest_ordering import OrderBy
from models_library.users import UserID
from pydantic import NonNegativeInt
from servicelib.utils import logged_gather
from simcore_postgres_database.webserver_models import ProjectType as ProjectTypeDB

from ..catalog.client import get_services_for_user_in_product
from . import projects_api
from ._permalink_api import update_or_pop_permalink_in_project
from .db import ProjectDBAPI
from .models import ProjectDict, ProjectTypeAPI


async def _append_fields(
    request: web.Request,
    *,
    user_id: UserID,
    project: ProjectDict,
    is_template: bool,
    model_schema_cls: type[OutputSchema],
):
    # state
    await projects_api.add_project_states_for_user(
        user_id=user_id,
        project=project,
        is_template=is_template,
        app=request.app,
    )

    # permalink
    await update_or_pop_permalink_in_project(request, project)

    # validate
    return model_schema_cls.parse_obj(project).data(exclude_unset=True)


async def list_projects(
    request: web.Request,
    user_id: UserID,
    product_name: str,
    project_type: ProjectTypeAPI,
    show_hidden: bool,
    offset: NonNegativeInt,
    limit: int,
    search: str | None,
    order_by: OrderBy,
    folder_id: FolderID | None,
) -> tuple[list[ProjectDict], int]:
    app = request.app
    db = ProjectDBAPI.get_from_app_context(app)

    user_available_services: list[dict] = await get_services_for_user_in_product(
        app, user_id, product_name, only_key_versions=True
    )

    db_projects, db_project_types, total_number_projects = await db.list_projects(
        user_id=user_id,
        product_name=product_name,
        filter_by_project_type=ProjectTypeAPI.to_project_type_db(project_type),
        filter_by_services=user_available_services,
        offset=offset,
        limit=limit,
        include_hidden=show_hidden,
        search=search,
        order_by=order_by,
        folder_id=folder_id,
    )

    projects: list[ProjectDict] = await logged_gather(
        *(
            _append_fields(
                request,
                user_id=user_id,
                project=prj,
                is_template=prj_type == ProjectTypeDB.TEMPLATE,
                model_schema_cls=ProjectListItem,
            )
            for prj, prj_type in zip(db_projects, db_project_types)
        ),
        reraise=True,
        max_concurrency=100,
    )

    return projects, total_number_projects


async def get_project(
    request: web.Request,
    user_id: UserID,
    product_name: str,
    project_uuid: ProjectID,
    project_type: ProjectTypeAPI,
):
    raise NotImplementedError
