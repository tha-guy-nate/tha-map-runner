import pytest


@pytest.fixture
def rows() -> list[dict]:
    return [
        {"Org BK": "school-001", "Start Date": "08/15"},
        {"Org BK": "school-002", "Start Date": "08/16"},
        {"Org BK": "school-003", "Start Date": "08/17"},
    ]


@pytest.fixture
def json_items() -> list[dict]:
    return [
        {
            "sourcedId": "school-001",
            "name": "Lincoln Elementary",
            "parent": {"sourcedId": "dist-A"},
        },
        {
            "sourcedId": "school-002",
            "name": "Roosevelt Middle",
            "parent": {"sourcedId": "dist-A"},
        },
    ]


@pytest.fixture
def mapping() -> dict[str, str]:
    return {
        "Org Name": "name",
        "Parent BK": "parent.sourcedId",
    }
