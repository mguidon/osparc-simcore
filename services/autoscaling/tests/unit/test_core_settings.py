# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-variable

import datetime
import json
import os

import pytest
from faker import Faker
from pydantic import ValidationError
from pytest_simcore.helpers.monkeypatch_envs import EnvVarsDict, setenvs_from_dict
from simcore_service_autoscaling.core.settings import (
    ApplicationSettings,
    EC2InstancesSettings,
)
from types_aiobotocore_ec2.literals import InstanceTypeType


def test_ec2_instances_settings(app_environment: EnvVarsDict):
    settings = EC2InstancesSettings.create_from_envs()
    assert isinstance(settings.EC2_INSTANCES_ALLOWED_TYPES, dict)


@pytest.fixture
def instance_type_with_invalid_boot_script(
    mock_env_devel_environment: EnvVarsDict,
    monkeypatch: pytest.MonkeyPatch,
    faker: Faker,
    aws_allowed_ec2_instance_type_names: list[InstanceTypeType],
) -> EnvVarsDict:
    return setenvs_from_dict(
        monkeypatch,
        {
            "EC2_INSTANCES_ALLOWED_TYPES": json.dumps(
                {
                    ec2_type_name: {
                        "ami_id": faker.pystr(),
                        "custom_boot_scripts": ['ls"'],
                    }
                    for ec2_type_name in aws_allowed_ec2_instance_type_names
                }
            ),
        },
    )


def test_ec2_instances_settings_with_invalid_custom_script_raises(
    app_environment: EnvVarsDict, instance_type_with_invalid_boot_script: EnvVarsDict
):
    with pytest.raises(ValidationError):
        EC2InstancesSettings.create_from_envs()


def test_settings(app_environment: EnvVarsDict):
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_ACCESS
    assert settings.AUTOSCALING_EC2_INSTANCES
    assert settings.AUTOSCALING_NODES_MONITORING is None
    assert settings.AUTOSCALING_DASK is None
    assert settings.AUTOSCALING_RABBITMQ
    assert settings.AUTOSCALING_REDIS


def test_settings_dynamic_mode(enabled_dynamic_mode: EnvVarsDict):
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_ACCESS
    assert settings.AUTOSCALING_SSM_ACCESS
    assert settings.AUTOSCALING_EC2_INSTANCES
    assert settings.AUTOSCALING_NODES_MONITORING
    assert settings.AUTOSCALING_DASK is None
    assert settings.AUTOSCALING_RABBITMQ
    assert settings.AUTOSCALING_REDIS


def test_settings_computational_mode(enabled_computational_mode: EnvVarsDict):
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_ACCESS
    assert settings.AUTOSCALING_SSM_ACCESS
    assert settings.AUTOSCALING_EC2_INSTANCES
    assert settings.AUTOSCALING_NODES_MONITORING is None
    assert settings.AUTOSCALING_DASK
    assert settings.AUTOSCALING_RABBITMQ
    assert settings.AUTOSCALING_REDIS


def test_defining_both_computational_and_dynamic_modes_is_invalid_and_raises(
    enabled_dynamic_mode: EnvVarsDict, enabled_computational_mode: EnvVarsDict
):
    with pytest.raises(ValidationError):
        ApplicationSettings.create_from_envs()


def test_invalid_EC2_INSTANCES_TIME_BEFORE_DRAINING(  # noqa: N802
    app_environment: EnvVarsDict, monkeypatch: pytest.MonkeyPatch
):
    setenvs_from_dict(monkeypatch, {"EC2_INSTANCES_TIME_BEFORE_DRAINING": "1:05:00"})
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_INSTANCES
    assert settings.AUTOSCALING_EC2_INSTANCES.EC2_INSTANCES_TIME_BEFORE_DRAINING
    assert (
        datetime.timedelta(minutes=1)
        == settings.AUTOSCALING_EC2_INSTANCES.EC2_INSTANCES_TIME_BEFORE_DRAINING
    )
    setenvs_from_dict(monkeypatch, {"EC2_INSTANCES_TIME_BEFORE_DRAINING": "-1:05:00"})
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_INSTANCES
    assert (
        datetime.timedelta(seconds=10)
        == settings.AUTOSCALING_EC2_INSTANCES.EC2_INSTANCES_TIME_BEFORE_DRAINING
    )


def test_invalid_EC2_INSTANCES_TIME_BEFORE_TERMINATION(  # noqa: N802
    app_environment: EnvVarsDict, monkeypatch: pytest.MonkeyPatch
):
    setenvs_from_dict(monkeypatch, {"EC2_INSTANCES_TIME_BEFORE_TERMINATION": "1:05:00"})
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_INSTANCES
    assert settings.AUTOSCALING_EC2_INSTANCES.EC2_INSTANCES_TIME_BEFORE_TERMINATION
    assert (
        datetime.timedelta(minutes=59)
        == settings.AUTOSCALING_EC2_INSTANCES.EC2_INSTANCES_TIME_BEFORE_TERMINATION
    )
    setenvs_from_dict(
        monkeypatch, {"EC2_INSTANCES_TIME_BEFORE_TERMINATION": "-1:05:00"}
    )
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_INSTANCES
    assert (
        datetime.timedelta(minutes=0)
        == settings.AUTOSCALING_EC2_INSTANCES.EC2_INSTANCES_TIME_BEFORE_TERMINATION
    )


def test_EC2_INSTANCES_ALLOWED_TYPES_valid(  # noqa: N802
    app_environment: EnvVarsDict, monkeypatch: pytest.MonkeyPatch, faker: Faker
):
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_INSTANCES


def test_EC2_INSTANCES_ALLOWED_TYPES_passing_invalid_image_tags(  # noqa: N802
    app_environment: EnvVarsDict, monkeypatch: pytest.MonkeyPatch, faker: Faker
):
    # passing an invalid image tag name will fail
    setenvs_from_dict(
        monkeypatch,
        {
            "EC2_INSTANCES_ALLOWED_TYPES": json.dumps(
                {
                    "t2.micro": {
                        "ami_id": faker.pystr(),
                        "pre_pull_images": ["io.simcore.some234.cool-"],
                    }
                }
            )
        },
    )
    with pytest.raises(ValidationError):
        ApplicationSettings.create_from_envs()


def test_EC2_INSTANCES_ALLOWED_TYPES_passing_valid_image_tags(  # noqa: N802
    app_environment: EnvVarsDict, monkeypatch: pytest.MonkeyPatch, faker: Faker
):
    # passing a valid will pass
    setenvs_from_dict(
        monkeypatch,
        {
            "EC2_INSTANCES_ALLOWED_TYPES": json.dumps(
                {
                    "t2.micro": {
                        "ami_id": faker.pystr(),
                        "pre_pull_images": [
                            "nginx:latest",
                            "itisfoundation/my-very-nice-service:latest",
                            "simcore/services/dynamic/another-nice-one:2.4.5",
                            "asd",
                        ],
                    }
                }
            ),
        },
    )
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_INSTANCES
    assert next(
        iter(settings.AUTOSCALING_EC2_INSTANCES.EC2_INSTANCES_ALLOWED_TYPES.values())
    ).pre_pull_images == [
        "nginx:latest",
        "itisfoundation/my-very-nice-service:latest",
        "simcore/services/dynamic/another-nice-one:2.4.5",
        "asd",
    ]


def test_EC2_INSTANCES_ALLOWED_TYPES_empty_not_allowed(  # noqa: N802
    app_environment: EnvVarsDict, monkeypatch: pytest.MonkeyPatch
):
    assert app_environment["AUTOSCALING_EC2_INSTANCES"] == "{}"
    monkeypatch.setenv("EC2_INSTANCES_ALLOWED_TYPES", "{}")

    # test child settings
    with pytest.raises(ValidationError) as err_info:
        EC2InstancesSettings.create_from_envs()

    assert err_info.value.errors()[0]["loc"] == ("EC2_INSTANCES_ALLOWED_TYPES",)


def test_EC2_INSTANCES_ALLOWED_TYPES_empty_not_allowed_with_main_field_env_var(  # noqa: N802
    app_environment: EnvVarsDict, monkeypatch: pytest.MonkeyPatch
):
    assert os.environ["AUTOSCALING_EC2_INSTANCES"] == "{}"
    monkeypatch.setenv("EC2_INSTANCES_ALLOWED_TYPES", "{}")

    # now as part of AUTOSCALING_EC2_INSTANCES: EC2InstancesSettings | None
    with pytest.raises(ValidationError) as exc_before:
        ApplicationSettings.create_from_envs(AUTOSCALING_EC2_INSTANCES={})

    with pytest.raises(ValidationError) as exc_after:
        ApplicationSettings.create_from_envs()

    assert exc_before.value.errors() == exc_after.value.errors()


def test_EC2_INSTANCES_ALLOWED_TYPES_empty_not_allowed_without_main_field_env_var(  # noqa: N802
    app_environment: EnvVarsDict, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("AUTOSCALING_EC2_INSTANCES")
    monkeypatch.setenv("EC2_INSTANCES_ALLOWED_TYPES", "{}")

    # removing any value for AUTOSCALING_EC2_INSTANCES
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_INSTANCES is None


def test_invalid_instance_names(
    app_environment: EnvVarsDict, monkeypatch: pytest.MonkeyPatch, faker: Faker
):
    settings = ApplicationSettings.create_from_envs()
    assert settings.AUTOSCALING_EC2_INSTANCES

    # passing an invalid image tag name will fail
    setenvs_from_dict(
        monkeypatch,
        {
            "EC2_INSTANCES_ALLOWED_TYPES": json.dumps(
                {faker.pystr(): {"ami_id": faker.pystr(), "pre_pull_images": []}}
            )
        },
    )
    with pytest.raises(ValidationError):
        ApplicationSettings.create_from_envs()
