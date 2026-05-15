# tha-map-runner

[![CI](https://github.com/tha-guy-nate/tha-map-runner/actions/workflows/ci.yml/badge.svg)](https://github.com/tha-guy-nate/tha-map-runner/actions/workflows/ci.yml)

A small Python library that joins a list of row dicts with a lookup source on a key, projecting values into flat row columns via a mapping config.

Think "left join between rows and a lookup source, with dotted-path projection on the source side."

## Install

```bash
pip install tha-map-runner
```

## Quick start

```python
from tha_map_runner import ThaMap

rows = [
    {"Org BK": "school-001", "Start Date": "08/15"},
    {"Org BK": "school-002", "Start Date": "08/16"},
]

api_response = [
    {"sourcedId": "school-001", "name": "Lincoln Elementary", "parent": {"sourcedId": "dist-A"}},
    {"sourcedId": "school-002", "name": "Roosevelt Middle",   "parent": {"sourcedId": "dist-A"}},
]

mapper = ThaMap()
enriched = mapper.enrich_rows(
    rows=rows,
    source=api_response,
    mapping={
        "Org Name":  "name",
        "Parent BK": "parent.sourcedId",
    },
    row_key="Org BK",
    source_key="sourcedId",
)
```

## How it works

1. Builds an index of `source` on `source_key` — O(n+m), no nested loops
2. For each row, looks up a match by `row[row_key]`
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
    source,                            # list of dicts to join against
    mapping,                           # {"output_column": "dotted.path"}
    row_key,                           # column name in rows to match on
    source_key,                        # field in source to match on
    *,
    on_no_match="skip",                # "skip" | "error" | "blank"
    allow_empty_source=False,          # if True, empty source is not an error
    skip_statuses=["error", "warning"],# rows with these statuses are passed through
) -> list[dict]
```

Results are also stored in `mapper.rows`.

### `on_no_match`

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
runner.rows = mapper.enrich_rows(
    rows=runner.rows,
    source=api_response,
    mapping={"Org Name": "name", "District": "parent.sourcedId"},
    row_key="Org BK",
    source_key="sourcedId",
)

runner.write("Step 2 of 2", "output.csv")
```

## License

MIT
