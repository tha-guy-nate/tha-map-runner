from __future__ import annotations

import warnings

from .errors import MapperError
from .paths import resolve_path

_HOW = {"left", "inner", "anti"}
_ON_NO_MATCH = {"skip", "error", "blank"}


class ThaMap:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def enrich_rows(
        self,
        rows: list[dict],
        source: list[dict],
        mapping: dict[str, str],
        row_key: str = "",
        source_key: str = "",
        *,
        keys: list[dict[str, str]] | None = None,
        how: str = "left",
        on_no_match: str = "skip",
        allow_empty_source: bool = False,
        skip_statuses: list[str] | None = None,
    ) -> list[dict]:
        if how not in _HOW:
            raise MapperError(f"how must be one of {sorted(_HOW)}, got {how!r}")
        if on_no_match not in _ON_NO_MATCH:
            raise MapperError(
                f"on_no_match must be one of {sorted(_ON_NO_MATCH)}, got {on_no_match!r}"
            )
        if keys is not None:
            if not keys:
                raise MapperError("keys must not be empty")
        elif not row_key or not source_key:
            raise MapperError("provide either keys or both row_key and source_key")

        statuses_to_skip = set(
            skip_statuses if skip_statuses is not None else ["error", "warning"]
        )

        if not source:
            if not allow_empty_source:
                raise MapperError("source is empty — pass allow_empty_source=True to allow this")
            if how == "inner":
                self.rows = []
                return []
            result = [row.copy() for row in rows]
            self.rows = result
            return result

        index: dict[object, dict] = {}
        if keys is not None:
            for item in source:
                k: object = tuple(resolve_path(item, kd["source_key"]) for kd in keys)
                if k in index:
                    warnings.warn(
                        f"Duplicate composite key {k!r} in source; using last occurrence",
                        stacklevel=2,
                    )
                index[k] = item
        else:
            for item in source:
                k = resolve_path(item, source_key)
                if k in index:
                    warnings.warn(
                        f"Duplicate {source_key!r} value {k!r} in source; using last occurrence",
                        stacklevel=2,
                    )
                index[k] = item

        output: list[dict] = []
        for row in rows:
            if row.get("row status") in statuses_to_skip:
                output.append(row.copy())
                continue

            if keys is not None:
                key_val: object = tuple(row.get(kd["row_key"]) for kd in keys)
            else:
                key_val = row.get(row_key)
            match = index.get(key_val)

            if how == "anti":
                if match is None:
                    output.append(row.copy())
                continue

            if match is None:
                if how == "inner":
                    continue
                new_row = row.copy()
                if on_no_match == "error":
                    if keys is not None:
                        msg = "No match for " + ", ".join(
                            f"{kd['row_key']}={row.get(kd['row_key'])!r}" for kd in keys
                        )
                    else:
                        msg = f"No match for {row_key}={key_val!r}"
                    new_row["row status"] = "error"
                    new_row["message"] = msg
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

        self.rows = output
        return output

    def enrich_from_ddb(
        self,
        rows: list[dict],
        ddb_result: dict[str, dict[str, dict]],
        row_key: str,
        mapping: dict[str, str],
        *,
        table_name: str = "",
        table_name_col: str = "",
        how: str = "left",
        on_no_match: str = "skip",
        skip_statuses: list[str] | None = None,
    ) -> list[dict]:
        if how not in _HOW:
            raise MapperError(f"how must be one of {sorted(_HOW)}, got {how!r}")
        if on_no_match not in _ON_NO_MATCH:
            raise MapperError(
                f"on_no_match must be one of {sorted(_ON_NO_MATCH)}, got {on_no_match!r}"
            )
        if bool(table_name) == bool(table_name_col):
            raise MapperError("provide exactly one of table_name or table_name_col")

        statuses_to_skip = set(
            skip_statuses if skip_statuses is not None else ["error", "warning"]
        )

        fixed_index: dict[object, dict] = {}
        if table_name:
            if table_name not in ddb_result:
                raise MapperError(f"table {table_name!r} not found in ddb_result")
            fixed_index = {
                pk: record
                for pk, record in ddb_result[table_name].items()
                if not record.get("not_found") and "error" not in record
            }

        output: list[dict] = []
        for row in rows:
            if row.get("row status") in statuses_to_skip:
                output.append(row.copy())
                continue

            key_val = row.get(row_key)

            if table_name_col:
                tbl = str(row.get(table_name_col) or "")
                record = ddb_result.get(tbl, {}).get(key_val)  # type: ignore[arg-type]
                match = (
                    record if record and not record.get("not_found") and "error" not in record
                    else None
                )
            else:
                match = fixed_index.get(key_val)

            if how == "anti":
                if match is None:
                    output.append(row.copy())
                continue

            if match is None:
                if how == "inner":
                    continue
                new_row = row.copy()
                if on_no_match == "error":
                    tbl_label = row.get(table_name_col, "") if table_name_col else table_name
                    new_row["row status"] = "error"
                    new_row["message"] = f"No match for {row_key}={key_val!r} in {tbl_label!r}"
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

        self.rows = output
        return output
