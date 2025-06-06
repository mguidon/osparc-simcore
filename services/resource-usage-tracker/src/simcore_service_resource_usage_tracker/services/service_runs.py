# pylint: disable=too-many-arguments
from datetime import UTC, datetime, timedelta

import shortuuid
from aws_library.s3 import SimcoreS3API
from models_library.api_schemas_resource_usage_tracker.credit_transactions import (
    WalletTotalCredits,
)
from models_library.api_schemas_resource_usage_tracker.service_runs import (
    OsparcCreditsAggregatedByServiceGet,
    OsparcCreditsAggregatedUsagesPage,
    ServiceRunGet,
    ServiceRunPage,
)
from models_library.api_schemas_storage.storage_schemas import S3BucketName
from models_library.products import ProductName
from models_library.projects import ProjectID
from models_library.resource_tracker import (
    CreditTransactionStatus,
    ServiceResourceUsagesFilters,
    ServicesAggregatedUsagesTimePeriod,
    ServicesAggregatedUsagesType,
)
from models_library.rest_ordering import OrderBy
from models_library.users import UserID
from models_library.wallets import WalletID
from pydantic import AnyUrl, TypeAdapter
from sqlalchemy.ext.asyncio import AsyncEngine

from .modules.db import service_runs_db

_PRESIGNED_LINK_EXPIRATION_SEC = 7200


async def list_service_runs(
    db_engine: AsyncEngine,
    *,
    user_id: UserID,
    product_name: ProductName,
    wallet_id: WalletID | None = None,
    access_all_wallet_usage: bool = False,
    filters: ServiceResourceUsagesFilters | None = None,
    transaction_status: CreditTransactionStatus | None = None,
    project_id: ProjectID | None = None,
    offset: int = 0,
    limit: int = 20,
    order_by: OrderBy | None = None,
) -> ServiceRunPage:
    started_from = None
    started_until = None
    if filters:
        started_from = filters.started_at.from_
        started_until = filters.started_at.until

    # Situation when we want to see all usage of a specific user (ex. for Non billable product)
    if wallet_id is None and access_all_wallet_usage is False:
        (
            total_service_runs,
            service_runs_db_model,
        ) = await service_runs_db.list_service_runs_by_product_and_user_and_wallet(
            db_engine,
            product_name=product_name,
            user_id=user_id,
            wallet_id=None,
            started_from=started_from,
            started_until=started_until,
            transaction_status=transaction_status,
            project_id=project_id,
            offset=offset,
            limit=limit,
            order_by=order_by,
        )
    # Situation when accountant user can see all users usage of the wallet
    elif wallet_id and access_all_wallet_usage is True:
        (
            total_service_runs,
            service_runs_db_model,
        ) = await service_runs_db.list_service_runs_by_product_and_user_and_wallet(
            db_engine,
            product_name=product_name,
            user_id=None,
            wallet_id=wallet_id,
            started_from=started_from,
            started_until=started_until,
            transaction_status=transaction_status,
            project_id=project_id,
            offset=offset,
            limit=limit,
            order_by=order_by,
        )
    # Situation when regular user can see only his usage of the wallet
    elif wallet_id and access_all_wallet_usage is False:
        (
            total_service_runs,
            service_runs_db_model,
        ) = await service_runs_db.list_service_runs_by_product_and_user_and_wallet(
            db_engine,
            product_name=product_name,
            user_id=user_id,
            wallet_id=wallet_id,
            started_from=started_from,
            started_until=started_until,
            transaction_status=transaction_status,
            project_id=project_id,
            offset=offset,
            limit=limit,
            order_by=order_by,
        )
    else:
        msg = "wallet_id and access_all_wallet_usage parameters must be specified together"
        raise ValueError(msg)

    service_runs_api_model: list[ServiceRunGet] = []
    for service in service_runs_db_model:
        service_runs_api_model.append(
            ServiceRunGet.model_construct(
                service_run_id=service.service_run_id,
                wallet_id=service.wallet_id,
                wallet_name=service.wallet_name,
                user_id=service.user_id,
                user_email=service.user_email,
                project_id=service.project_id,
                project_name=service.project_name,
                project_tags=service.project_tags,
                root_parent_project_id=service.root_parent_project_id,
                root_parent_project_name=service.root_parent_project_name,
                node_id=service.node_id,
                node_name=service.node_name,
                service_key=service.service_key,
                service_version=service.service_version,
                service_type=service.service_type,
                started_at=service.started_at,
                stopped_at=service.stopped_at,
                service_run_status=service.service_run_status,
                credit_cost=service.osparc_credits,
                transaction_status=service.transaction_status,
            )
        )

    return ServiceRunPage(service_runs_api_model, total_service_runs)


async def export_service_runs(
    s3_client: SimcoreS3API,
    *,
    bucket_name: str,
    s3_region: str,
    user_id: UserID,
    product_name: ProductName,
    db_engine: AsyncEngine,
    wallet_id: WalletID | None = None,
    access_all_wallet_usage: bool = False,
    order_by: OrderBy | None = None,
    filters: ServiceResourceUsagesFilters | None = None,
) -> AnyUrl:
    started_from = filters.started_at.from_ if filters else None
    started_until = filters.started_at.until if filters else None

    # Create S3 key name
    s3_bucket_name = TypeAdapter(S3BucketName).validate_python(bucket_name)
    # NOTE: su stands for "service usage"
    file_name = f"su_{shortuuid.uuid()}.csv"
    s3_object_key = (
        f"resource-usage-tracker-service-runs/{datetime.now(tz=UTC).date()}/{file_name}"
    )

    # Export CSV to S3
    await service_runs_db.export_service_runs_table_to_s3(
        db_engine,
        product_name=product_name,
        s3_bucket_name=s3_bucket_name,
        s3_key=s3_object_key,
        s3_region=s3_region,
        user_id=user_id if access_all_wallet_usage is False else None,
        wallet_id=wallet_id,
        started_from=started_from,
        started_until=started_until,
        order_by=order_by,
    )

    # Create presigned S3 link
    return await s3_client.create_single_presigned_download_link(
        bucket=s3_bucket_name,
        object_key=s3_object_key,
        expiration_secs=_PRESIGNED_LINK_EXPIRATION_SEC,
    )


async def sum_project_wallet_total_credits(
    db_engine: AsyncEngine,
    *,
    product_name: ProductName,
    wallet_id: WalletID,
    project_id: ProjectID,
    transaction_status: CreditTransactionStatus | None = None,
) -> WalletTotalCredits:
    return await service_runs_db.sum_project_wallet_total_credits(
        db_engine,
        product_name=product_name,
        wallet_id=wallet_id,
        project_id=project_id,
        transaction_status=transaction_status,
    )


async def get_osparc_credits_aggregated_usages_page(
    user_id: UserID,
    product_name: ProductName,
    db_engine: AsyncEngine,
    aggregated_by: ServicesAggregatedUsagesType,
    time_period: ServicesAggregatedUsagesTimePeriod,
    wallet_id: WalletID,
    access_all_wallet_usage: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> OsparcCreditsAggregatedUsagesPage:
    current_datetime = datetime.now(tz=UTC)
    started_from = current_datetime - timedelta(days=time_period.value)

    assert aggregated_by == ServicesAggregatedUsagesType.services  # nosec

    (
        count_output_list_db,
        output_list_db,
    ) = await service_runs_db.get_osparc_credits_aggregated_by_service(
        db_engine,
        product_name=product_name,
        user_id=user_id if access_all_wallet_usage is False else None,
        wallet_id=wallet_id,
        offset=offset,
        limit=limit,
        started_from=started_from,
        started_until=None,
    )
    output_api_model: list[OsparcCreditsAggregatedByServiceGet] = []
    for item in output_list_db:
        output_api_model.append(
            OsparcCreditsAggregatedByServiceGet.model_construct(
                osparc_credits=item.osparc_credits,
                service_key=item.service_key,
                running_time_in_hours=item.running_time_in_hours,
            )
        )

    return OsparcCreditsAggregatedUsagesPage(output_api_model, count_output_list_db)
