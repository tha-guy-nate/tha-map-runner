import warnings

import pytest

from tha_map_runner import MapperError, map_json_to_rows


def test_basic_mapping(rows, json_items, mapping) -> None:
    result = map_json_to_rows(rows, json_items, mapping, row_key="Org BK", json_key="sourcedId")
    matched = [r for r in result if r.get("Org Name")]
    assert matched[0]["Org Name"] == "Lincoln Elementary"
    assert matched[0]["Parent BK"] == "dist-A"
    assert matched[1]["Org Name"] == "Roosevelt Middle"


def test_dotted_path_resolved(rows, json_items, mapping) -> None:
    result = map_json_to_rows(rows, json_items, mapping, row_key="Org BK", json_key="sourcedId")
    assert result[0]["Parent BK"] == "dist-A"


def test_original_columns_preserved(rows, json_items, mapping) -> None:
    result = map_json_to_rows(rows, json_items, mapping, row_key="Org BK", json_key="sourcedId")
    assert result[0]["Start Date"] == "08/15"


def test_input_not_mutated(rows, json_items, mapping) -> None:
    original = [r.copy() for r in rows]
    map_json_to_rows(rows, json_items, mapping, row_key="Org BK", json_key="sourcedId")
    assert rows == original


def test_returns_new_list(rows, json_items, mapping) -> None:
    result = map_json_to_rows(rows, json_items, mapping, row_key="Org BK", json_key="sourcedId")
    assert result is not rows


def test_row_count_preserved(rows, json_items, mapping) -> None:
    result = map_json_to_rows(rows, json_items, mapping, row_key="Org BK", json_key="sourcedId")
    assert len(result) == len(rows)


# --- on_no_match="skip" (default) ---

def test_no_match_skip_leaves_row_unchanged(rows, json_items, mapping) -> None:
    result = map_json_to_rows(rows, json_items, mapping, row_key="Org BK", json_key="sourcedId")
    no_match = result[2]  # school-003 not in json_items
    assert "Org Name" not in no_match
    assert no_match.get("row status") != "error"


# --- on_no_match="error" ---

def test_no_match_error_sets_row_status(rows, json_items, mapping) -> None:
    result = map_json_to_rows(
        rows, json_items, mapping, row_key="Org BK", json_key="sourcedId", on_no_match="error"
    )
    no_match = result[2]
    assert no_match["row status"] == "error"
    assert "school-003" in no_match["message"]


def test_no_match_error_blanks_mapping_fields(rows, json_items, mapping) -> None:
    result = map_json_to_rows(
        rows, json_items, mapping, row_key="Org BK", json_key="sourcedId", on_no_match="error"
    )
    no_match = result[2]
    assert no_match["Org Name"] == ""
    assert no_match["Parent BK"] == ""


# --- on_no_match="blank" ---

def test_no_match_blank_adds_empty_columns(rows, json_items, mapping) -> None:
    result = map_json_to_rows(
        rows, json_items, mapping, row_key="Org BK", json_key="sourcedId", on_no_match="blank"
    )
    no_match = result[2]
    assert no_match["Org Name"] == ""
    assert no_match["Parent BK"] == ""
    assert no_match.get("row status") != "error"


def test_invalid_on_no_match_raises(rows, json_items, mapping) -> None:
    with pytest.raises(MapperError, match="on_no_match"):
        map_json_to_rows(
            rows, json_items, mapping, row_key="Org BK", json_key="sourcedId", on_no_match="bad"
        )


# --- allow_empty_json ---

def test_empty_json_raises_by_default(rows, mapping) -> None:
    with pytest.raises(MapperError, match="empty"):
        map_json_to_rows(rows, [], mapping, row_key="Org BK", json_key="sourcedId")


def test_empty_json_allowed(rows, mapping) -> None:
    result = map_json_to_rows(
        rows, [], mapping, row_key="Org BK", json_key="sourcedId", allow_empty_json=True
    )
    assert len(result) == len(rows)
    assert "Org Name" not in result[0]


# --- error row pass-through ---

def test_error_rows_passed_through(json_items, mapping) -> None:
    rows = [
        {"Org BK": "school-001", "row status": "error", "message": "bad row"},
    ]
    result = map_json_to_rows(rows, json_items, mapping, row_key="Org BK", json_key="sourcedId")
    assert result[0]["row status"] == "error"
    assert result[0]["message"] == "bad row"
    assert "Org Name" not in result[0]


# --- duplicate json_key warning ---

def test_duplicate_json_key_warns(rows, mapping) -> None:
    dupes = [
        {"sourcedId": "school-001", "name": "First"},
        {"sourcedId": "school-001", "name": "Second"},
    ]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = map_json_to_rows(rows, dupes, mapping, row_key="Org BK", json_key="sourcedId")
    assert any("Duplicate" in str(w.message) for w in caught)
    assert result[0]["Org Name"] == "Second"


# --- edge cases ---

def test_empty_rows_returns_empty(json_items, mapping) -> None:
    result = map_json_to_rows([], json_items, mapping, row_key="Org BK", json_key="sourcedId")
    assert result == []


def test_missing_path_in_json_gives_empty_string(rows, mapping) -> None:
    items = [{"sourcedId": "school-001", "name": "Lincoln"}]  # no "parent" key
    result = map_json_to_rows(rows[:1], items, mapping, row_key="Org BK", json_key="sourcedId")
    assert result[0]["Parent BK"] == ""


def test_row_missing_row_key_treated_as_no_match(json_items, mapping) -> None:
    rows = [{"Start Date": "08/15"}]  # no "Org BK"
    result = map_json_to_rows(
        rows, json_items, mapping, row_key="Org BK", json_key="sourcedId", on_no_match="blank"
    )
    assert result[0]["Org Name"] == ""
