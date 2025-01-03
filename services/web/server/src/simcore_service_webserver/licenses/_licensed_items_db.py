""" Database API

    - Adds a layer to the postgres API with a focus on the projects comments

"""

import logging
from typing import cast

from aiohttp import web
from models_library.licensed_items import (
    LicensedItemDB,
    LicensedItemID,
    LicensedItemUpdateDB,
    LicensedResourceType,
)
from models_library.products import ProductName
from models_library.resource_tracker import PricingPlanId
from models_library.rest_ordering import OrderBy, OrderDirection
from pydantic import NonNegativeInt
from simcore_postgres_database.models.licensed_items import licensed_items
from simcore_postgres_database.utils_repos import (
    pass_or_acquire_connection,
    transaction_context,
)
from sqlalchemy import asc, desc, func
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import select

from ..db.plugin import get_asyncpg_engine
from .errors import LicensedItemNotFoundError

_logger = logging.getLogger(__name__)


_SELECTION_ARGS = (
    licensed_items.c.licensed_item_id,
    licensed_items.c.name,
    licensed_items.c.licensed_resource_type,
    licensed_items.c.pricing_plan_id,
    licensed_items.c.product_name,
    licensed_items.c.created,
    licensed_items.c.modified,
)

assert set(LicensedItemDB.model_fields) == {c.name for c in _SELECTION_ARGS}  # nosec


async def create(
    app: web.Application,
    connection: AsyncConnection | None = None,
    *,
    product_name: ProductName,
    name: str,
    licensed_resource_type: LicensedResourceType,
    pricing_plan_id: PricingPlanId,
) -> LicensedItemDB:
    async with transaction_context(get_asyncpg_engine(app), connection) as conn:
        result = await conn.stream(
            licensed_items.insert()
            .values(
                name=name,
                licensed_resource_type=licensed_resource_type,
                pricing_plan_id=pricing_plan_id,
                product_name=product_name,
                created=func.now(),
                modified=func.now(),
            )
            .returning(*_SELECTION_ARGS)
        )
        row = await result.first()
        return LicensedItemDB.model_validate(row)


async def list_(
    app: web.Application,
    connection: AsyncConnection | None = None,
    *,
    product_name: ProductName,
    offset: NonNegativeInt,
    limit: NonNegativeInt,
    order_by: OrderBy,
) -> tuple[int, list[LicensedItemDB]]:
    base_query = (
        select(*_SELECTION_ARGS)
        .select_from(licensed_items)
        .where(licensed_items.c.product_name == product_name)
    )

    # Select total count from base_query
    subquery = base_query.subquery()
    count_query = select(func.count()).select_from(subquery)

    # Ordering and pagination
    if order_by.direction == OrderDirection.ASC:
        list_query = base_query.order_by(asc(getattr(licensed_items.c, order_by.field)))
    else:
        list_query = base_query.order_by(
            desc(getattr(licensed_items.c, order_by.field))
        )
    list_query = list_query.offset(offset).limit(limit)

    async with pass_or_acquire_connection(get_asyncpg_engine(app), connection) as conn:
        total_count = await conn.scalar(count_query)

        result = await conn.stream(list_query)
        items: list[LicensedItemDB] = [
            LicensedItemDB.model_validate(row) async for row in result
        ]

        return cast(int, total_count), items


async def get(
    app: web.Application,
    connection: AsyncConnection | None = None,
    *,
    licensed_item_id: LicensedItemID,
    product_name: ProductName,
) -> LicensedItemDB:
    base_query = (
        select(*_SELECTION_ARGS)
        .select_from(licensed_items)
        .where(
            (licensed_items.c.licensed_item_id == licensed_item_id)
            & (licensed_items.c.product_name == product_name)
        )
    )

    async with pass_or_acquire_connection(get_asyncpg_engine(app), connection) as conn:
        result = await conn.stream(base_query)
        row = await result.first()
        if row is None:
            raise LicensedItemNotFoundError(licensed_item_id=licensed_item_id)
        return LicensedItemDB.model_validate(row)


async def update(
    app: web.Application,
    connection: AsyncConnection | None = None,
    *,
    product_name: ProductName,
    licensed_item_id: LicensedItemID,
    updates: LicensedItemUpdateDB,
) -> LicensedItemDB:
    # NOTE: at least 'touch' if updated_values is empty
    _updates = {
        **updates.dict(exclude_unset=True),
        "modified": func.now(),
    }

    async with transaction_context(get_asyncpg_engine(app), connection) as conn:
        result = await conn.stream(
            licensed_items.update()
            .values(**_updates)
            .where(
                (licensed_items.c.licensed_item_id == licensed_item_id)
                & (licensed_items.c.product_name == product_name)
            )
            .returning(*_SELECTION_ARGS)
        )
        row = await result.first()
        if row is None:
            raise LicensedItemNotFoundError(licensed_item_id=licensed_item_id)
        return LicensedItemDB.model_validate(row)


async def delete(
    app: web.Application,
    connection: AsyncConnection | None = None,
    *,
    licensed_item_id: LicensedItemID,
    product_name: ProductName,
) -> None:
    async with transaction_context(get_asyncpg_engine(app), connection) as conn:
        await conn.execute(
            licensed_items.delete().where(
                (licensed_items.c.licensed_item_id == licensed_item_id)
                & (licensed_items.c.product_name == product_name)
            )
        )
