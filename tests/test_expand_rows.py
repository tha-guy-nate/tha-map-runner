import pytest

from tha_map_runner import MapperError, ThaMap


@pytest.fixture
def mapper() -> ThaMap:
    return ThaMap()


@pytest.fixture
def district_rows() -> list[dict]:
    return [
        {"District BK": "100", "District Name": "Springfield USD"},
        {"District BK": "200", "District Name": "Shelbyville USD"},
    ]


@pytest.fixture
def assessment_records() -> list[dict]:
    return [
        {"District BK": "100", "id": "a1", "score": "85", "student": {"id": "s1"}},
        {"District BK": "100", "id": "a2", "score": "90", "student": {"id": "s2"}},
        {"District BK": "200", "id": "a3", "score": "78", "student": {"id": "s3"}},
    ]


@pytest.fixture
def mapping() -> dict[str, str]:
    return {
        "iODS ID": "id",
        "Score": "score",
        "Student ID": "student.id",
    }


def test_expand_basic(mapper, district_rows, assessment_records, mapping):
    result = mapper.expand_rows(
        district_rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    assert len(result) == 3


def test_expand_one_to_many(mapper, district_rows, assessment_records, mapping):
    result = mapper.expand_rows(
        district_rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    district_100 = [r for r in result if r["District BK"] == "100"]
    assert len(district_100) == 2


def test_expand_field_mapping(mapper, district_rows, assessment_records, mapping):
    result = mapper.expand_rows(
        district_rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    ids = {r["iODS ID"] for r in result}
    assert ids == {"a1", "a2", "a3"}


def test_expand_dotted_path(mapper, district_rows, assessment_records, mapping):
    result = mapper.expand_rows(
        district_rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    student_ids = {r["Student ID"] for r in result}
    assert student_ids == {"s1", "s2", "s3"}


def test_expand_parent_fields_preserved(mapper, district_rows, assessment_records, mapping):
    result = mapper.expand_rows(
        district_rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    for row in result:
        assert "District Name" in row


def test_expand_input_not_mutated(mapper, district_rows, assessment_records, mapping):
    original = [r.copy() for r in district_rows]
    mapper.expand_rows(
        district_rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    assert district_rows == original


def test_expand_returns_new_list(mapper, district_rows, assessment_records, mapping):
    result = mapper.expand_rows(
        district_rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    assert result is not district_rows


def test_expand_sets_self_rows(mapper, district_rows, assessment_records, mapping):
    result = mapper.expand_rows(
        district_rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    assert mapper.rows is result


def test_expand_no_match_skip(mapper, mapping):
    rows = [{"District BK": "999", "District Name": "No Match"}]
    source = [{"District BK": "100", "id": "a1", "score": "85", "student": {"id": "s1"}}]
    result = mapper.expand_rows(
        rows, source, mapping,
        row_key="District BK", source_key="District BK",
        how="left", on_no_match="skip",
    )
    assert len(result) == 1
    assert result[0]["District BK"] == "999"
    assert "iODS ID" not in result[0]


def test_expand_no_match_error(mapper, mapping):
    rows = [{"District BK": "999", "District Name": "No Match"}]
    source = [{"District BK": "100", "id": "a1", "score": "85", "student": {"id": "s1"}}]
    result = mapper.expand_rows(
        rows, source, mapping,
        row_key="District BK", source_key="District BK",
        how="left", on_no_match="error",
    )
    assert len(result) == 1
    assert result[0]["row status"] == "error"
    assert "999" in result[0]["message"]
    assert result[0]["iODS ID"] == ""


def test_expand_no_match_blank(mapper, mapping):
    rows = [{"District BK": "999", "District Name": "No Match"}]
    source = [{"District BK": "100", "id": "a1", "score": "85", "student": {"id": "s1"}}]
    result = mapper.expand_rows(
        rows, source, mapping,
        row_key="District BK", source_key="District BK",
        how="left", on_no_match="blank",
    )
    assert len(result) == 1
    assert result[0].get("row status") != "error"
    assert result[0]["iODS ID"] == ""


def test_expand_how_inner_drops_unmatched(mapper, mapping):
    rows = [
        {"District BK": "100", "District Name": "Springfield"},
        {"District BK": "999", "District Name": "No Match"},
    ]
    source = [{"District BK": "100", "id": "a1", "score": "85", "student": {"id": "s1"}}]
    result = mapper.expand_rows(
        rows, source, mapping,
        row_key="District BK", source_key="District BK",
        how="inner",
    )
    assert len(result) == 1
    assert result[0]["District BK"] == "100"


def test_expand_how_anti(mapper, mapping):
    rows = [
        {"District BK": "100", "District Name": "Springfield"},
        {"District BK": "999", "District Name": "No Match"},
    ]
    source = [{"District BK": "100", "id": "a1", "score": "85", "student": {"id": "s1"}}]
    result = mapper.expand_rows(
        rows, source, mapping,
        row_key="District BK", source_key="District BK",
        how="anti",
    )
    assert len(result) == 1
    assert result[0]["District BK"] == "999"


def test_expand_skip_error_rows(mapper, assessment_records, mapping):
    rows = [
        {"District BK": "100", "row status": "error", "message": "bad creds"},
        {"District BK": "200"},
    ]
    result = mapper.expand_rows(
        rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    error_rows = [r for r in result if r.get("row status") == "error"]
    assert len(error_rows) == 1
    assert error_rows[0]["District BK"] == "100"
    normal_rows = [r for r in result if r.get("row status") != "error"]
    assert len(normal_rows) == 1
    assert normal_rows[0]["iODS ID"] == "a3"


def test_expand_skip_warning_rows(mapper, assessment_records, mapping):
    rows = [{"District BK": "100", "row status": "warning"}, {"District BK": "200"}]
    result = mapper.expand_rows(
        rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
    )
    assert len(result) == 2
    warning_rows = [r for r in result if r.get("row status") == "warning"]
    assert len(warning_rows) == 1


def test_expand_custom_skip_statuses(mapper, assessment_records, mapping):
    rows = [
        {"District BK": "100", "row status": "pending"},
        {"District BK": "200"},
    ]
    result = mapper.expand_rows(
        rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
        skip_statuses=["pending"],
    )
    pending_rows = [r for r in result if r.get("row status") == "pending"]
    assert len(pending_rows) == 1
    expanded = [r for r in result if "iODS ID" in r]
    assert len(expanded) == 1
    assert expanded[0]["iODS ID"] == "a3"


def test_expand_empty_skip_statuses(mapper, assessment_records, mapping):
    rows = [{"District BK": "100", "row status": "error"}]
    result = mapper.expand_rows(
        rows, assessment_records, mapping,
        row_key="District BK", source_key="District BK",
        skip_statuses=[],
    )
    assert len(result) == 2


def test_expand_empty_source_raises(mapper, district_rows, mapping):
    with pytest.raises(MapperError, match="source is empty"):
        mapper.expand_rows(
            district_rows, [], mapping,
            row_key="District BK", source_key="District BK",
        )


def test_expand_empty_source_allow_left(mapper, district_rows, mapping):
    result = mapper.expand_rows(
        district_rows, [], mapping,
        row_key="District BK", source_key="District BK",
        allow_empty_source=True,
    )
    assert len(result) == len(district_rows)
    assert result is not district_rows


def test_expand_empty_source_allow_inner(mapper, district_rows, mapping):
    result = mapper.expand_rows(
        district_rows, [], mapping,
        row_key="District BK", source_key="District BK",
        allow_empty_source=True, how="inner",
    )
    assert result == []


def test_expand_invalid_how(mapper, district_rows, assessment_records, mapping):
    with pytest.raises(MapperError, match="how must be one of"):
        mapper.expand_rows(
            district_rows, assessment_records, mapping,
            row_key="District BK", source_key="District BK",
            how="outer",
        )


def test_expand_invalid_on_no_match(mapper, district_rows, assessment_records, mapping):
    with pytest.raises(MapperError, match="on_no_match must be one of"):
        mapper.expand_rows(
            district_rows, assessment_records, mapping,
            row_key="District BK", source_key="District BK",
            on_no_match="raise",
        )
