import warnings

from .errors import MapperError
from .paths import resolve_path

_ON_NO_MATCH = {"skip", "error", "blank"}


def map_json_to_rows(
    rows: list[dict],
    json_items: list[dict],
    mapping: dict[str, str],
    row_key: str,
    json_key: str,
    *,
    on_no_match: str = "skip",
    allow_empty_json: bool = False,
) -> list[dict]:
    if on_no_match not in _ON_NO_MATCH:
        raise MapperError(f"on_no_match must be one of {sorted(_ON_NO_MATCH)}, got {on_no_match!r}")

    if not json_items:
        if allow_empty_json:
            return [row.copy() for row in rows]
        raise MapperError("json_items is empty — pass allow_empty_json=True to allow this")

    index: dict[object, dict] = {}
    for item in json_items:
        key = item.get(json_key)
        if key in index:
            warnings.warn(
                f"Duplicate {json_key!r} value {key!r} in json_items; using last occurrence",
                stacklevel=2,
            )
        index[key] = item

    output: list[dict] = []
    for row in rows:
        if row.get("row status") == "error":
            output.append(row.copy())
            continue

        key_val = row.get(row_key)
        match = index.get(key_val)

        if match is None:
            new_row = row.copy()
            if on_no_match == "error":
                new_row["row status"] = "error"
                new_row["message"] = f"No JSON match for {row_key}={key_val!r}"
                for field in mapping:
                    new_row[field] = ""
            elif on_no_match == "blank":
                for field in mapping:
                    new_row[field] = ""
            output.append(new_row)
            continue

        new_row = row.copy()
        for field, path in mapping.items():
            value = resolve_path(match, path)
            new_row[field] = "" if value is None else value

        output.append(new_row)

    return output
