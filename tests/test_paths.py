import pytest

from tha_map_runner import MapperError, exclude, include
from tha_map_runner.paths import resolve_mapping_value, resolve_path


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


def test_list_traversal_single_item() -> None:
    obj = {"scoreResults": [{"result": "85"}]}
    assert resolve_path(obj, "scoreResults.result") == "85"


def test_list_traversal_multi_item() -> None:
    obj = {"scoreResults": [{"result": "85"}, {"result": "90"}]}
    assert resolve_path(obj, "scoreResults.result") == ["85", "90"]


def test_list_traversal_deeply_nested() -> None:
    obj = {"a": [{"b": {"c": 42}}]}
    assert resolve_path(obj, "a.b.c") == 42


def test_list_traversal_missing_key_in_item() -> None:
    obj = {"a": [{"b": 1}, {"x": 2}]}
    assert resolve_path(obj, "a.b") == [1, None]


def test_list_traversal_non_dict_item() -> None:
    obj = {"a": ["string", 99]}
    assert resolve_path(obj, "a.b") == [None, None]


def test_list_traversal_nested_list_of_lists() -> None:
    obj = {"a": [[{"c": 1}, "skip"], [{"c": 2}]]}
    assert resolve_path(obj, "a.c") == [1, None, 2]


# --- resolve_mapping_value ---


def test_mapping_value_scalar_path() -> None:
    assert resolve_mapping_value({"name": "Alice"}, "name") == "Alice"


def test_mapping_value_empty_string_returns_whole_match() -> None:
    match = {"name": "Alice", "role": "admin"}
    assert resolve_mapping_value(match, "") == match


def test_mapping_value_dict_builds_sub_dict() -> None:
    match = {"name": "Alice", "role": "admin", "team": "eng"}
    spec = {"who": "name", "job": "role"}
    assert resolve_mapping_value(match, spec) == {"who": "Alice", "job": "admin"}


def test_mapping_value_dict_can_nest_whole_match() -> None:
    match = {"name": "Alice"}
    assert resolve_mapping_value(match, {"full": ""}) == {"full": match}


def test_mapping_value_list_is_shorthand_dict_keyed_by_path() -> None:
    match = {"name": "Alice", "role": "admin"}
    assert resolve_mapping_value(match, ["name", "role"]) == {"name": "Alice", "role": "admin"}


def test_mapping_value_set_excludes_keys() -> None:
    match = {"name": "Alice", "role": "admin", "ssn": "123-45-6789"}
    assert resolve_mapping_value(match, {"ssn"}) == {"name": "Alice", "role": "admin"}


def test_mapping_value_set_exclude_none_matching_keeps_everything() -> None:
    match = {"name": "Alice", "role": "admin"}
    assert resolve_mapping_value(match, {"nonexistent"}) == match


def test_mapping_value_missing_path_gives_empty_string() -> None:
    assert resolve_mapping_value({"name": "Alice"}, "no.such.path") == ""


def test_mapping_value_invalid_type_raises() -> None:
    with pytest.raises(MapperError, match="invalid mapping value"):
        resolve_mapping_value({"name": "Alice"}, 5)  # type: ignore[arg-type]


# --- include / exclude helpers ---


def test_include_returns_list() -> None:
    assert include("age", "gender.code") == ["age", "gender.code"]


def test_include_empty() -> None:
    assert include() == []


def test_exclude_returns_set() -> None:
    assert exclude("ssn", "internal_id") == {"ssn", "internal_id"}


def test_exclude_empty() -> None:
    assert exclude() == set()


def test_include_used_as_mapping_value() -> None:
    match = {"age": 42, "gender": {"code": "F"}}
    assert resolve_mapping_value(match, include("age", "gender.code")) == {
        "age": 42,
        "gender.code": "F",
    }


def test_exclude_used_as_mapping_value() -> None:
    match = {"name": "Alice", "ssn": "123-45-6789"}
    assert resolve_mapping_value(match, exclude("ssn")) == {"name": "Alice"}
