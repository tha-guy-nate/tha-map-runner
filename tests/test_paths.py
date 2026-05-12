import pytest

from tha_map_runner.paths import resolve_path


def test_top_level_key() -> None:
    assert resolve_path({"name": "Alice"}, "name") == "Alice"


def test_nested_key() -> None:
    assert resolve_path({"parent": {"sourcedId": "dist-A"}}, "parent.sourcedId") == "dist-A"


def test_deeply_nested() -> None:
    obj = {"a": {"b": {"c": 42}}}
    assert resolve_path(obj, "a.b.c") == 42


def test_missing_key_returns_none() -> None:
    assert resolve_path({"name": "Alice"}, "email") is None


def test_missing_intermediate_key_returns_none() -> None:
    assert resolve_path({"a": {"b": 1}}, "a.x.c") is None


def test_non_dict_intermediate_returns_none() -> None:
    assert resolve_path({"a": "string"}, "a.b") is None


def test_empty_path_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        resolve_path({"a": 1}, "")


def test_none_value_returned() -> None:
    assert resolve_path({"key": None}, "key") is None
