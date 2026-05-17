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
        row_key: str,
        source_key: str,
        *,
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
        for item in source:
            key = item.get(source_key)
            if key in index:
                warnings.warn(
                    f"Duplicate {source_key!r} value {key!r} in source; using last occurrence",
                    stacklevel=2,
                )
            index[key] = item

        output: list[dict] = []
        for row in rows:
            if row.get("row status") in statuses_to_skip:
                output.append(row.copy())
                continue

            key_val = row.get(row_key)
            match = index.get(key_val)

            if how == "anti":
                if match is None:
                    output.append(row.copy())
                continue

            if match is None:
                if how == "inner":
                    continue
                # how == "left"
                new_row = row.copy()
                if on_no_match == "error":
                    new_row["row status"] = "error"
                    new_row["message"] = f"No match for {row_key}={key_val!r}"
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
