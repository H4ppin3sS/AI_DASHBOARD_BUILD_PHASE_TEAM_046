import pytest
pytest.importorskip("streamlit")
from core.scene_finder import _norm, _value, _resolve


def test_metadata_display():
    assert _value(None) == "missing"
    assert _value("unknown") == "unknown"


def test_zip_path_resolution():
    paths = ["images/a.jpg", "images/b.jpg"]
    assert _resolve("a.jpg", paths) == "images/a.jpg"
    assert _resolve("missing.jpg", paths) is None
