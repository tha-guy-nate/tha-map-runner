# tha-map-runner

[![CI](https://github.com/tha-guy-nate/tha-map-runner/actions/workflows/ci.yml/badge.svg)](https://github.com/tha-guy-nate/tha-map-runner/actions/workflows/ci.yml)

A small Python library that joins a list of row dicts with a lookup source, projecting values into flat row columns via a mapping config.

Supports single-key and composite-key joins, left/inner/anti modes, and dotted-path projection into arbitrarily nested source data.

## Install

```bash
pip install tha-map-runner
```

## Quick start

```python
from tha_map_runner import ThaMap

mapper = ThaMap()
```

**Single-key** — match rows against a lookup source on one field:

```python
rows = [
    {"Org BK": "school-001", "Start Date": "08/15"},
    {"Org BK": "school-002", "Start Date": "08/16"},
]

api_response = [
    {"sourcedId": "school-001", "name": "Lincoln Elementary", "parent": {"sourcedId": "dist-A"}},
    {"sourcedId": "school-002", "name": "Roosevelt Middle",   "parent": {"sourcedId": "dist-A"}},
]

enriched = mapper.enrich_rows(
    rows,
    source=api_response,
    mapping={
        "Org Name":  "name",
        "Parent BK": "parent.sourcedId",  # dotted path into nested source
    },
    row_key="Org BK",
    source_key="sourcedId",               # also supports dotted paths: "org.sourcedId"
)
```

**Composite-key** — all key pairs must match simultaneously (use when a single field is ambiguous):

```python
rows = [
    {"source_id": "s-001", "student": "Alice", "Term": "Fall"},
    {"source_id": "s-001", "student": "Bob",   "Term": "Fall"},
]

api_response = [
    {"org": {"id": "s-001"}, "profile": {"name": "Alice"}, "grade": "A"},
    {"org": {"id": "s-001"}, "profile": {"name": "Bob"},   "grade": "B"},
]

enriched = mapper.enrich_rows(
    rows,
    source=api_response,
    mapping={"Grade": "grade"},
    keys=[
        {"row_key": "source_id", "source_key": "org.id"},
        {"row_key": "student",   "source_key": "profile.name"},
    ],
)
```

## How it works

1. Builds an index of `source` keyed by the match field(s) — O(n+m), no nested loops
2. For each row, looks up a match; composite-key mode requires all pairs to agree
3. Walks dotted paths (`"parent.sourcedId"`) into the matched source entry
4. Projects resolved values into new columns on a copy of the row
5. Returns a new list — input is never mutated

Rows whose `row status` is in `skip_statuses` are passed through unchanged.

## API

### `ThaMap`

```python
ThaMap()
```

### `mapper.enrich_rows()`

```python
mapper.enrich_rows(
    rows,                              # list of row dicts
    source,                            # list of dicts to join against (any nesting depth)
    mapping,                           # {"output_column": "dotted.path"}
    row_key="",                        # column name in rows to match on (single-key mode)
    source_key="",                     # dotted path in source to match on (single-key mode)
    *,
    keys=None,                         # composite-key mode: [{"row_key": "...", "source_key": "..."}, ...]
    how="left",                        # "left" | "inner" | "anti"
    on_no_match="skip",                # "skip" | "error" | "blank"  (left only)
    allow_empty_source=False,          # if True, empty source is not an error
    skip_statuses=["error", "warning"],# rows with these statuses are passed through
) -> list[dict]
```

Provide either `row_key` + `source_key` (single-key) or `keys` (composite-key) — not both.

Both `source_key` and the `source_key` entries in `keys` support dotted paths into arbitrarily nested source data (e.g. `"org.sourcedId"`). `row_key` always matches against the flat row dict.

**Composite-key example** — match only when both fields agree simultaneously:

```python
mapper.enrich_rows(
    rows,
    api_response,
    mapping={"Grade": "grade", "Score": "score"},
    keys=[
        {"row_key": "source_id", "source_key": "org.sourcedId"},
        {"row_key": "student",   "source_key": "student.profile.name"},
    ],
)
```

Results are also stored in `mapper.rows`.

### `mapper.enrich_from_ddb()`

Enriches rows from a `fetch_by_pk` result (the `{table_name: {pk: record}}` shape returned by `tha-aws-runner`'s `ThaDdb.fetch_by_pk`). No `tha-aws-runner` import required — just pass the dict.

```python
mapper.enrich_from_ddb(
    rows,                              # list of row dicts
    ddb_result,                        # {table_name: {pk: record}} from ThaDdb.fetch_by_pk
    row_key,                           # column name in rows to match on (matched against pk)
    mapping,                           # {"output_column": "dotted.path"}
    *,
    table_name="",                     # scope lookup to one table (all rows same table)
    table_name_col="",                 # row column holding the table name (mixed-table rows)
    how="left",                        # "left" | "inner" | "anti"
    on_no_match="skip",                # "skip" | "error" | "blank"  (left only)
    skip_statuses=["error", "warning"],# rows with these statuses are passed through
) -> list[dict]
```

Provide exactly one of `table_name` or `table_name_col` — not both, not neither.

`not_found` and `error` entries in `ddb_result` are filtered automatically and treated as missing matches.

**Single-table** — all rows look up against the same table:

```python
enriched = mapper.enrich_from_ddb(rows, all_ddb, "user_id", {"Name": "name"}, table_name="users_table")
```

**Multi-table (chained)** — one call per table, each scoped explicitly:

```python
all_ddb = {**ddb.batch_fetch_by_pk("users_table", user_ids, key_name="id", key_type="S"),
           **ddb.batch_fetch_by_pk("orders_table", order_ids, key_name="id", key_type="S")}

enriched = mapper.enrich_from_ddb(rows, all_ddb, "user_id", {"Name": "name"}, table_name="users_table")
enriched = mapper.enrich_from_ddb(enriched, all_ddb, "order_id", {"Status": "status"}, table_name="orders_table")
```

**Mixed-table rows** — rows have different tables; use `table_name_col` to route each row:

```python
rows = [
    {"pk": "user-001", "source_table": "users_table"},
    {"pk": "order-001", "source_table": "orders_table"},
]

enriched = mapper.enrich_from_ddb(rows, all_ddb, "pk", {"Name": "name"}, table_name_col="source_table")
```

Results are also stored in `mapper.rows`.

### `how`

| Value | Behaviour |
|---|---|
| `"left"` | All rows kept; unmatched rows handled by `on_no_match` |
| `"inner"` | Only matched rows kept; mapping applied |
| `"anti"` | Only unmatched rows kept; no mapping applied |

Rows whose `row status` is in `skip_statuses` are always passed through unchanged, regardless of `how`.

### `on_no_match` (left join only)

| Value | Behaviour |
|---|---|
| `"skip"` | Row is returned unchanged — no new columns added |
| `"error"` | `row status="error"`, `message=...`, mapping columns set to `""` |
| `"blank"` | Mapping columns set to `""`, row status untouched |

### `skip_statuses`

By default, rows already marked `row status="error"` or `row status="warning"` are passed through without processing. Override with any list:

```python
mapper.enrich_rows(..., skip_statuses=["error"])               # only skip errors
mapper.enrich_rows(..., skip_statuses=["error", "pending"])    # custom statuses
mapper.enrich_rows(..., skip_statuses=[])                      # process every row regardless
```

### Composing with `tha-csv-runner`

```python
from tha_csv_runner import ThaCSV
from tha_map_runner import ThaMap
import requests

runner = ThaCSV()
runner.read("Step 1 of 2", "input.csv", ["Org BK"])

api_response = requests.get(api_url).json()

mapper = ThaMap()
enriched = mapper.enrich_rows(
    rows=runner.rows,
    source=api_response,
    mapping={"Org Name": "name", "District": "parent.sourcedId"},
    row_key="Org BK",
    source_key="sourcedId",
)

runner.write("Step 2 of 2", "output.csv", rows=enriched)
```

### `mapper.expand_rows()`

Like `enrich_rows` but one-to-many: produces N output rows for a row with N matches in source. Use when source contains multiple records per row key (e.g. assessment records fetched per district via `batch_get_all`).

```python
mapper.expand_rows(
    rows,                              # list of row dicts
    source,                            # list of dicts to fan out against
    mapping,                           # {"output_column": "dotted.path"}
    *,
    row_key,                           # column name in rows to match on
    source_key,                        # dotted path in source to match on
    how="left",                        # "left" | "inner" | "anti"
    on_no_match="skip",                # "skip" | "error" | "blank"  (left only)
    allow_empty_source=False,          # if True, empty source is not an error
    skip_statuses=["error", "warning"],# rows with these statuses are passed through
) -> list[dict]
```

```python
# Fetch all assessments per district (returns flat list with "District BK" injected per record)
flat = runner.batch_get_all(token_rows, key_col="District BK", workers=4)

# Fan out district rows — one output row per assessment
expanded = mapper.expand_rows(
    district_rows,
    source=flat,
    mapping={
        "Assessment ID": "id",
        "Score":         "scoreResults[0].result",
    },
    row_key="District BK",
    source_key="District BK",
)
```

`how` and `on_no_match` behave identically to `enrich_rows`. Results stored in `mapper.rows`.

## Alternatives

This library is intentionally limited in scope — it handles one specific pattern: joining row dicts against a lookup list on a single key and projecting values via dotted paths. For more general needs:

- [**pandas**](https://pandas.pydata.org) — `DataFrame.merge()` covers join operations with far more flexibility (outer, multi-key, aggregations)
- [**glom**](https://glom.readthedocs.io) — powerful dotted-path access and transformation for arbitrarily nested Python data structures
- [**jmespath**](https://jmespath.org) — JSON path-style queries for extracting values from nested dicts

Choose this library when you're already working with `tha-*` row dicts and want to join them against a lookup list in one call — no DataFrame conversion, left/inner/anti join and projection in a single step.

## License

MIT
