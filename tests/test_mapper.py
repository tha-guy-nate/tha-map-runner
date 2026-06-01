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


def test_enrich_rows_dotted_source_key(mapper, rows, mapping):
    source = [
        {"meta": {"sourcedId": "school-001"}, "name": "Lincoln Elementary",
         "parent": {"sourcedId": "dist-A"}},
        {"meta": {"sourcedId": "school-002"}, "name": "Roosevelt Middle",
         "parent": {"sourcedId": "dist-A"}},
    ]
    result = mapper.enrich_rows(rows, source, mapping, "Org BK", "meta.sourcedId")
    assert result[0]["Org Name"] == "Lincoln Elementary"
    assert result[1]["Org Name"] == "Roosevelt Middle"


def test_row_missing_row_key_treated_as_no_match(
    mapper: ThaMap, json_items: list[dict], mapping: dict[str, str]
) -> None:
    rows = [{"Start Date": "08/15"}]  # no "Org BK"
    result = mapper.enrich_rows(
        rows, json_items, mapping, "Org BK", "sourcedId", on_no_match="blank"
    )
    assert result[0]["Org Name"] == ""


# --- enrich_rows: composite keys (keys=) ---


@pytest.fixture
def mk_source() -> list[dict]:
    return [
        {"sourcedId": "s-001", "studentName": "Alice", "grade": "A", "score": 95},
        {"sourcedId": "s-001", "studentName": "Bob", "grade": "B", "score": 80},
        {"sourcedId": "s-002", "studentName": "Alice", "grade": "A+", "score": 98},
    ]


@pytest.fixture
def mk_rows() -> list[dict]:
    return [
        {"source_id": "s-001", "student": "Alice", "Start Date": "08/15"},
        {"source_id": "s-001", "student": "Bob", "Start Date": "08/16"},
        {"source_id": "s-002", "student": "Alice", "Start Date": "08/17"},
        {"source_id": "s-999", "student": "Ghost", "Start Date": "08/18"},
    ]


@pytest.fixture
def mk_keys() -> list[dict]:
    return [
        {"row_key": "source_id", "source_key": "sourcedId"},
        {"row_key": "student", "source_key": "studentName"},
    ]


@pytest.fixture
def mk_mapping() -> dict:
    return {"Grade": "grade", "Score": "score"}


def test_keys_happy(mapper, mk_source, mk_rows, mk_keys, mk_mapping):
    result = mapper.enrich_rows(mk_rows, mk_source, mk_mapping, keys=mk_keys)
    assert result[0]["Grade"] == "A"
    assert result[0]["Score"] == 95
    assert result[1]["Grade"] == "B"
    assert result[2]["Grade"] == "A+"
    assert result[2]["Score"] == 98


def test_keys_partial_match_is_no_match(mapper, mk_source, mk_keys, mk_mapping):
    rows = [{"source_id": "s-001", "student": "Nobody", "Start Date": "08/15"}]
    result = mapper.enrich_rows(rows, mk_source, mk_mapping, keys=mk_keys)
    assert "Grade" not in result[0]


def test_keys_original_columns_preserved(mapper, mk_source, mk_rows, mk_keys, mk_mapping):
    result = mapper.enrich_rows(mk_rows, mk_source, mk_mapping, keys=mk_keys)
    assert result[0]["Start Date"] == "08/15"


def test_keys_input_not_mutated(mapper, mk_source, mk_rows, mk_keys, mk_mapping):
    original = [r.copy() for r in mk_rows]
    mapper.enrich_rows(mk_rows, mk_source, mk_mapping, keys=mk_keys)
    assert mk_rows == original


def test_keys_returns_new_list(mapper, mk_source, mk_rows, mk_keys, mk_mapping):
    result = mapper.enrich_rows(mk_rows, mk_source, mk_mapping, keys=mk_keys)
    assert result is not mk_rows


def test_keys_stores_rows(mapper, mk_source, mk_rows, mk_keys, mk_mapping):
    result = mapper.enrich_rows(mk_rows, mk_source, mk_mapping, keys=mk_keys)
    assert mapper.rows is result


def test_keys_inner(mapper, mk_source, mk_rows, mk_keys, mk_mapping):
    result = mapper.enrich_rows(mk_rows, mk_source, mk_mapping, keys=mk_keys, how="inner")
    assert len(result) == 3
    assert all("Grade" in r for r in result)


def test_keys_anti(mapper, mk_source, mk_rows, mk_keys, mk_mapping):
    result = mapper.enrich_rows(mk_rows, mk_source, mk_mapping, keys=mk_keys, how="anti")
    assert len(result) == 1
    assert result[0]["student"] == "Ghost"


def test_keys_on_no_match_error(mapper, mk_source, mk_rows, mk_keys, mk_mapping):
    result = mapper.enrich_rows(
        mk_rows, mk_source, mk_mapping, keys=mk_keys, on_no_match="error"
    )
    no_match = result[3]
    assert no_match["row status"] == "error"
    assert "Ghost" in no_match["message"]
    assert no_match["Grade"] == ""


def test_keys_on_no_match_blank(mapper, mk_source, mk_rows, mk_keys, mk_mapping):
    result = mapper.enrich_rows(
        mk_rows, mk_source, mk_mapping, keys=mk_keys, on_no_match="blank"
    )
    no_match = result[3]
    assert no_match["Grade"] == ""
    assert no_match.get("row status") != "error"


def test_keys_skip_statuses(mapper, mk_source, mk_keys, mk_mapping):
    rows = [{"source_id": "s-001", "student": "Alice", "row status": "error", "message": "bad"}]
    result = mapper.enrich_rows(rows, mk_source, mk_mapping, keys=mk_keys)
    assert "Grade" not in result[0]
    assert result[0]["row status"] == "error"


def test_keys_empty_raises(mapper, mk_source, mk_rows, mk_mapping):
    with pytest.raises(MapperError, match="keys must not be empty"):
        mapper.enrich_rows(mk_rows, mk_source, mk_mapping, keys=[])


def test_keys_missing_row_key_and_source_key_raises(mapper, mk_source, mk_rows, mk_mapping):
    with pytest.raises(MapperError, match="provide either keys"):
        mapper.enrich_rows(mk_rows, mk_source, mk_mapping)


def test_keys_empty_source_raises_by_default(mapper, mk_rows, mk_keys, mk_mapping):
    with pytest.raises(MapperError, match="empty"):
        mapper.enrich_rows(mk_rows, [], mk_mapping, keys=mk_keys)


def test_keys_allow_empty_source(mapper, mk_rows, mk_keys, mk_mapping):
    result = mapper.enrich_rows(mk_rows, [], mk_mapping, keys=mk_keys, allow_empty_source=True)
    assert len(result) == len(mk_rows)
    assert "Grade" not in result[0]


def test_keys_dotted_source_key(mapper, mk_mapping):
    source = [
        {"org": {"sourcedId": "s-001"}, "student": {"name": "Alice"}, "grade": "A", "score": 95},
    ]
    rows = [{"source_id": "s-001", "student": "Alice"}]
    keys = [
        {"row_key": "source_id", "source_key": "org.sourcedId"},
        {"row_key": "student", "source_key": "student.name"},
    ]
    result = mapper.enrich_rows(rows, source, mk_mapping, keys=keys)
    assert result[0]["Grade"] == "A"
    assert result[0]["Score"] == 95


def test_keys_duplicate_warns(mapper, mk_keys, mk_mapping):
    dupes = [
        {"sourcedId": "s-001", "studentName": "Alice", "grade": "A"},
        {"sourcedId": "s-001", "studentName": "Alice", "grade": "B"},
    ]
    rows = [{"source_id": "s-001", "student": "Alice"}]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = mapper.enrich_rows(rows, dupes, mk_mapping, keys=mk_keys)
    assert any("Duplicate" in str(w.message) for w in caught)
    assert result[0]["Grade"] == "B"


# --- enrich_from_ddb ---


@pytest.fixture
def ddb_result() -> dict:
    return {
        "users_table": {
            "user-001": {"status": None, "message": None, "pk": "user-001", "table": "users_table", "data": {"name": "Alice", "role": "admin"}},  # noqa: E501
            "user-002": {"status": None, "message": None, "pk": "user-002", "table": "users_table", "data": {"name": "Bob", "role": "member"}},  # noqa: E501
            "user-003": {"status": "error", "message": "Item not found", "pk": "user-003", "table": "users_table", "data": None},  # noqa: E501
        },
        "orders_table": {
            "order-001": {"status": None, "message": None, "pk": "order-001", "table": "orders_table", "data": {"status": "shipped"}},  # noqa: E501
        },
    }


@pytest.fixture
def ddb_rows() -> list[dict]:
    return [
        {"user_id": "user-001", "Start Date": "08/15"},
        {"user_id": "user-002", "Start Date": "08/16"},
        {"user_id": "user-003", "Start Date": "08/17"},
    ]


@pytest.fixture
def ddb_mapping() -> dict:
    return {"Name": "name", "Role": "role"}


def test_enrich_from_ddb_happy(mapper, ddb_result, ddb_rows, ddb_mapping):
    result = mapper.enrich_from_ddb(
        ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table"
    )
    assert result[0]["Name"] == "Alice"
    assert result[0]["Role"] == "admin"
    assert result[1]["Name"] == "Bob"


def test_enrich_from_ddb_original_columns_preserved(mapper, ddb_result, ddb_rows, ddb_mapping):
    result = mapper.enrich_from_ddb(
        ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table"
    )
    assert result[0]["Start Date"] == "08/15"


def test_enrich_from_ddb_not_found_treated_as_no_match(mapper, ddb_result, ddb_rows, ddb_mapping):
    result = mapper.enrich_from_ddb(
        ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table"
    )
    assert "Name" not in result[2]


def test_enrich_from_ddb_error_treated_as_no_match(mapper, ddb_rows, ddb_mapping):
    ddb_result = {
        "users_table": {
            "user-001": {"status": None, "message": None, "pk": "user-001", "table": "users_table", "data": {"name": "Alice", "role": "admin"}},  # noqa: E501
            "user-002": {"status": "error", "message": "AccessDeniedException", "pk": "user-002", "table": "users_table", "data": None},  # noqa: E501
            "user-003": {"status": "error", "message": "Item not found", "pk": "user-003", "table": "users_table", "data": None},  # noqa: E501
        }
    }
    result = mapper.enrich_from_ddb(
        ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table"
    )
    assert result[0]["Name"] == "Alice"
    assert "Name" not in result[1]
    assert "Name" not in result[2]


def test_enrich_from_ddb_multi_table(mapper, ddb_result, ddb_mapping):
    rows = [{"user_id": "user-001", "order_id": "order-001", "Start Date": "08/15"}]
    result = mapper.enrich_from_ddb(
        rows, ddb_result, "user_id", ddb_mapping, table_name="users_table"
    )
    result2 = mapper.enrich_from_ddb(
        result, ddb_result, "order_id", {"Status": "status"}, table_name="orders_table"
    )
    assert result2[0]["Name"] == "Alice"
    assert result2[0]["Status"] == "shipped"


def test_enrich_from_ddb_missing_table_raises(mapper, ddb_result, ddb_rows, ddb_mapping):
    with pytest.raises(MapperError, match="not found in ddb_result"):
        mapper.enrich_from_ddb(ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="bad_table")


def test_enrich_from_ddb_no_table_arg_raises(mapper, ddb_result, ddb_rows, ddb_mapping):
    with pytest.raises(MapperError, match="exactly one of table_name or table_name_col"):
        mapper.enrich_from_ddb(ddb_rows, ddb_result, "user_id", ddb_mapping)


def test_enrich_from_ddb_both_table_args_raises(mapper, ddb_result, ddb_rows, ddb_mapping):
    with pytest.raises(MapperError, match="exactly one of table_name or table_name_col"):
        mapper.enrich_from_ddb(
            ddb_rows, ddb_result, "user_id", ddb_mapping,
            table_name="users_table", table_name_col="tbl",
        )


def test_enrich_from_ddb_inner(mapper, ddb_result, ddb_rows, ddb_mapping):
    result = mapper.enrich_from_ddb(
        ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table", how="inner"
    )
    assert len(result) == 2
    assert all(r["user_id"] in ("user-001", "user-002") for r in result)


def test_enrich_from_ddb_anti(mapper, ddb_result, ddb_rows, ddb_mapping):
    result = mapper.enrich_from_ddb(
        ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table", how="anti"
    )
    assert len(result) == 1
    assert result[0]["user_id"] == "user-003"


def test_enrich_from_ddb_on_no_match_error(mapper, ddb_result, ddb_rows, ddb_mapping):
    result = mapper.enrich_from_ddb(
        ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table", on_no_match="error"
    )
    assert result[2]["row status"] == "error"
    assert "user-003" in result[2]["message"]


def test_enrich_from_ddb_on_no_match_blank(mapper, ddb_result, ddb_rows, ddb_mapping):
    result = mapper.enrich_from_ddb(
        ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table", on_no_match="blank"
    )
    assert result[2]["Name"] == ""
    assert result[2].get("row status") != "error"


def test_enrich_from_ddb_skip_statuses(mapper, ddb_result, ddb_mapping):
    rows = [{"user_id": "user-001", "row status": "error", "message": "bad"}]
    result = mapper.enrich_from_ddb(
        rows, ddb_result, "user_id", ddb_mapping, table_name="users_table"
    )
    assert "Name" not in result[0]
    assert result[0]["row status"] == "error"


def test_enrich_from_ddb_stores_rows(mapper, ddb_result, ddb_rows, ddb_mapping):
    result = mapper.enrich_from_ddb(
        ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table"
    )
    assert mapper.rows is result


def test_enrich_from_ddb_input_not_mutated(mapper, ddb_result, ddb_rows, ddb_mapping):
    original = [r.copy() for r in ddb_rows]
    mapper.enrich_from_ddb(ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table")
    assert ddb_rows == original


def test_enrich_from_ddb_invalid_how_raises(mapper, ddb_result, ddb_rows, ddb_mapping):
    with pytest.raises(MapperError, match="how"):
        mapper.enrich_from_ddb(
            ddb_rows, ddb_result, "user_id", ddb_mapping, table_name="users_table", how="outer"
        )


def test_enrich_from_ddb_invalid_on_no_match_raises(mapper, ddb_result, ddb_rows, ddb_mapping):
    with pytest.raises(MapperError, match="on_no_match"):
        mapper.enrich_from_ddb(
            ddb_rows, ddb_result, "user_id", ddb_mapping,
            table_name="users_table", on_no_match="bad",
        )


# --- enrich_from_ddb: table_name_col ---


def test_enrich_from_ddb_table_name_col_happy(mapper, ddb_result, ddb_mapping):
    rows = [
        {"user_id": "user-001", "tbl": "users_table", "Start Date": "08/15"},
        {"user_id": "user-002", "tbl": "users_table", "Start Date": "08/16"},
        {"user_id": "user-003", "tbl": "users_table", "Start Date": "08/17"},
    ]
    result = mapper.enrich_from_ddb(rows, ddb_result, "user_id", ddb_mapping, table_name_col="tbl")
    assert result[0]["Name"] == "Alice"
    assert result[1]["Name"] == "Bob"
    assert "Name" not in result[2]


def test_enrich_from_ddb_table_name_col_mixed_tables(mapper, ddb_result):
    rows = [
        {"pk": "user-001", "tbl": "users_table"},
        {"pk": "order-001", "tbl": "orders_table"},
    ]
    result = mapper.enrich_from_ddb(
        rows, ddb_result, "pk", {"Val": "name"}, table_name_col="tbl"
    )
    assert result[0]["Val"] == "Alice"
    result2 = mapper.enrich_from_ddb(
        rows, ddb_result, "pk", {"Val": "status"}, table_name_col="tbl"
    )
    assert result2[1]["Val"] == "shipped"


def test_enrich_from_ddb_table_name_col_missing_table_no_match(mapper, ddb_result, ddb_mapping):
    rows = [{"user_id": "user-001", "tbl": "nonexistent_table"}]
    result = mapper.enrich_from_ddb(
        rows, ddb_result, "user_id", ddb_mapping, table_name_col="tbl", on_no_match="blank"
    )
    assert result[0]["Name"] == ""


def test_enrich_from_ddb_table_name_col_not_found_no_match(mapper, ddb_result, ddb_mapping):
    rows = [{"user_id": "user-003", "tbl": "users_table"}]
    result = mapper.enrich_from_ddb(
        rows, ddb_result, "user_id", ddb_mapping, table_name_col="tbl"
    )
    assert "Name" not in result[0]


def test_enrich_from_ddb_table_name_col_error_treated_as_no_match(mapper, ddb_mapping):
    ddb_result = {
        "users_table": {
            "user-001": {"status": None, "message": None, "pk": "user-001", "table": "users_table", "data": {"name": "Alice", "role": "admin"}},  # noqa: E501
            "user-002": {"status": "error", "message": "AccessDeniedException", "pk": "user-002", "table": "users_table", "data": None},  # noqa: E501
        }
    }
    rows = [
        {"user_id": "user-001", "tbl": "users_table"},
        {"user_id": "user-002", "tbl": "users_table"},
    ]
    result = mapper.enrich_from_ddb(
        rows, ddb_result, "user_id", ddb_mapping, table_name_col="tbl"
    )
    assert result[0]["Name"] == "Alice"
    assert "Name" not in result[1]
