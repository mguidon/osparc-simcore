# TODO: W0611:Unused import ...
# pylint: disable=W0611
# TODO: W0613:Unused argument ...
# pylint: disable=W0613

import os

import pytest

from simcore_service_storage.datcore_wrapper import DatcoreWrapper


@pytest.mark.travis
async def test_datcore_list_files(python27_exec):
    api_token = os.environ.get("BF_API_KEY", "none")
    api_secret = os.environ.get("BF_API_SECRET", "none")
    dcw = DatcoreWrapper(api_token, api_secret, python27_exec)
    f = await dcw.list_files()
    print(f)
