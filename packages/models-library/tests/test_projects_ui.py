import pytest
from models_library.api_schemas_webserver.projects_ui import AnnotationUI
from pydantic_extra_types.color import Color


@pytest.mark.parametrize(
    "color_str,expected_color_str", [("#b7e28d", "#b7e28d"), ("Cyan", "#0ff")]
)
def test_annotation_color_serialized_to_hex(color_str, expected_color_str):
    m = AnnotationUI(type="text", color=Color(color_str), attributes={})
    assert (
        m.model_dump_json()
        == f'{{"type":"text","color":"{expected_color_str}","attributes":{{}}}}'
    )
