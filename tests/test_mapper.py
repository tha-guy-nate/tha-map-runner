import warnings

import pytest

from tha_map_runner import MapperError, ThaMap


@pytest.fixture
def mapper() -> ThaMap:
    return ThaMap()


def test_basic_mapping(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    matched = [r for r in result if r.get("Org Name")]
    assert matched[0]["Org Name"] == "Lincoln Elementary"
    assert matched[0]["Parent BK"] == "dist-A"
    assert matched[1]["Org Name"] == "Roosevelt Middle"


def test_dotted_path_resolved(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    assert result[0]["Parent BK"] == "dist-A"


def test_original_columns_preserved(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    assert result[0]["Start Date"] == "08/15"


def test_input_not_mutated(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    original = [r.copy() for r in rows]
    mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    assert rows == original


def test_returns_new_list(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    assert result is not rows


def test_row_count_preserved(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    assert len(result) == len(rows)


def test_enrich_rows_stores_rows(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    assert mapper.rows is result


# --- on_no_match="skip" (default) ---

def test_no_match_skip_leaves_row_unchanged(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    no_match = result[2]  # school-003 not in source
    assert "Org Name" not in no_match
    assert no_match.get("row status") != "error"


# --- on_no_match="error" ---

def test_no_match_error_sets_row_status(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(
        rows, json_items, mapping, "Org BK", "sourcedId", on_no_match="error"
    )
    no_match = result[2]
    assert no_match["row status"] == "error"
    assert "school-003" in no_match["message"]


def test_no_match_error_blanks_mapping_fields(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(
        rows, json_items, mapping, "Org BK", "sourcedId", on_no_match="error"
    )
    no_match = result[2]
    assert no_match["Org Name"] == ""
    assert no_match["Parent BK"] == ""


# --- on_no_match="blank" ---

def test_no_match_blank_adds_empty_columns(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(
        rows, json_items, mapping, "Org BK", "sourcedId", on_no_match="blank"
    )
    no_match = result[2]
    assert no_match["Org Name"] == ""
    assert no_match["Parent BK"] == ""
    assert no_match.get("row status") != "error"


def test_invalid_on_no_match_raises(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    with pytest.raises(MapperError, match="on_no_match"):
        mapper.enrich_rows([], json_items, mapping, "Org BK", "sourcedId", on_no_match="bad")


# --- how="inner" ---

def test_inner_keeps_only_matched_rows(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="inner")
    assert len(result) == 2
    assert all(r["Org BK"] in ("school-001", "school-002") for r in result)


def test_inner_applies_mapping(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="inner")
    assert result[0]["Org Name"] == "Lincoln Elementary"
    assert result[1]["Org Name"] == "Roosevelt Middle"


def test_inner_drops_unmatched(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="inner")
    assert not any(r["Org BK"] == "school-003" for r in result)


def test_inner_empty_source_allowed_returns_empty(
    rows: list[dict], mapper: ThaMap, mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(
        rows, [], mapping, "Org BK", "sourcedId", how="inner", allow_empty_source=True
    )
    assert result == []


def test_inner_passes_through_skip_status_rows(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    rows = [
        {"Org BK": "school-001", "row status": "error", "message": "bad"},
        {"Org BK": "school-002"},
    ]
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="inner")
    assert any(r.get("row status") == "error" for r in result)


def test_inner_stores_rows(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="inner")
    assert mapper.rows is result


# --- how="anti" ---

def test_anti_keeps_only_unmatched_rows(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="anti")
    assert len(result) == 1
    assert result[0]["Org BK"] == "school-003"


def test_anti_does_not_apply_mapping(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="anti")
    assert "Org Name" not in result[0]


def test_anti_row_unchanged(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="anti")
    assert result[0]["Start Date"] == "08/17"


def test_anti_empty_source_allowed_returns_all(
    rows: list[dict], mapper: ThaMap, mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(
        rows, [], mapping, "Org BK", "sourcedId", how="anti", allow_empty_source=True
    )
    assert len(result) == len(rows)


def test_anti_passes_through_skip_status_rows(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    rows = [
        {"Org BK": "school-001", "row status": "error", "message": "bad"},
        {"Org BK": "school-003"},
    ]
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="anti")
    assert any(r.get("row status") == "error" for r in result)
    assert any(r["Org BK"] == "school-003" for r in result)


def test_anti_stores_rows(
    rows: list[dict], mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId", how="anti")
    assert mapper.rows is result


def test_invalid_how_raises(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    with pytest.raises(MapperError, match="how"):
        mapper.enrich_rows([], json_items, mapping, "Org BK", "sourcedId", how="outer")


# --- allow_empty_source ---

def test_empty_source_raises_by_default(
    rows: list[dict], mapper: ThaMap, mapping: dict[str, str]
) -> None:
    with pytest.raises(MapperError, match="empty"):
        mapper.enrich_rows(rows, [], mapping, "Org BK", "sourcedId")


def test_empty_source_allowed(
    rows: list[dict], mapper: ThaMap, mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows(rows, [], mapping, "Org BK", "sourcedId", allow_empty_source=True)
    assert len(result) == len(rows)
    assert "Org Name" not in result[0]


# --- skip_statuses ---

def test_error_rows_skipped_by_default(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    rows = [{"Org BK": "school-001", "row status": "error", "message": "bad row"}]
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    assert result[0]["row status"] == "error"
    assert result[0]["message"] == "bad row"
    assert "Org Name" not in result[0]


def test_warning_rows_skipped_by_default(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    rows = [{"Org BK": "school-001", "row status": "warning", "message": "heads up"}]
    result = mapper.enrich_rows(rows, json_items, mapping, "Org BK", "sourcedId")
    assert result[0]["row status"] == "warning"
    assert "Org Name" not in result[0]


def test_custom_skip_statuses(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    rows = [{"Org BK": "school-001", "row status": "pending"}]
    result = mapper.enrich_rows(
        rows, json_items, mapping, "Org BK", "sourcedId", skip_statuses=["pending"]
    )
    assert "Org Name" not in result[0]


def test_empty_skip_statuses_processes_all(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    rows = [{"Org BK": "school-001", "row status": "error", "message": "bad row"}]
    result = mapper.enrich_rows(
        rows, json_items, mapping, "Org BK", "sourcedId", skip_statuses=[]
    )
    assert result[0]["Org Name"] == "Lincoln Elementary"


# --- duplicate source_key warning ---

def test_duplicate_source_key_warns(
    rows: list[dict], mapper: ThaMap, mapping: dict[str, str]
) -> None:
    dupes = [
        {"sourcedId": "school-001", "name": "First"},
        {"sourcedId": "school-001", "name": "Second"},
    ]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = mapper.enrich_rows(rows, dupes, mapping, "Org BK", "sourcedId")
    assert any("Duplicate" in str(w.message) for w in caught)
    assert result[0]["Org Name"] == "Second"


# --- edge cases ---

def test_empty_rows_returns_empty(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    result = mapper.enrich_rows([], json_items, mapping, "Org BK", "sourcedId")
    assert result == []


def test_missing_path_in_source_gives_empty_string(
    rows: list[dict], mapper: ThaMap, mapping: dict[str, str]
) -> None:
    source = [{"sourcedId": "school-001", "name": "Lincoln"}]  # no "parent" key
    result = mapper.enrich_rows(rows[:1], source, mapping, "Org BK", "sourcedId")
    assert result[0]["Parent BK"] == ""


def test_row_missing_row_key_treated_as_no_match(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    rows = [{"Start Date": "08/15"}]  # no "Org BK"
    result = mapper.enrich_rows(
        rows, json_items, mapping, "Org BK", "sourcedId", on_no_match="blank"
    )
    assert result[0]["Org Name"] == ""
