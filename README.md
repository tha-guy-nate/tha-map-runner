# tha-map-runner

[![CI](https://github.com/tha-guy-nate/tha-map-runner/actions/workflows/ci.yml/badge.svg)](https://github.com/tha-guy-nate/tha-map-runner/actions/workflows/ci.yml)

A small Python library that joins a list of row dicts with a list of JSON objects on a key, projecting nested JSON values into flat row columns via a mapping config.

Think "left join between rows and JSON, with dotted-path projection on the JSON side."

## Install

```bash
pip install tha-map-runner
```

## Quick start

```python
from tha_map_runner import map_json_to_rows

rows = [
    {"Org BK": "school-001", "Start Date": "08/15"},
    {"Org BK": "school-002", "Start Date": "08/16"},
]

api_response = [
    {"sourcedId": "school-001", "name": "Lincoln Elementary", "parent": {"sourcedId": "dist-A"}},
    {"sourcedId": "school-002", "name": "Roosevelt Middle",   "parent": {"sourcedId": "dist-A"}},
]

enriched = map_json_to_rows(
    rows=rows,
    json_items=api_response,
    mapping={
        "Org Name":  "name",
        "Parent BK": "parent.sourcedId",
    },
    row_key="Org BK",
    json_key="sourcedId",
)
```

## How it works

1. Builds an index of `json_items` on `json_key` — O(n+m), no nested loops
2. For each row, looks up a match by `row[row_key]`
3. Walks dotted paths (`"parent.sourcedId"`) into the matched JSON object
4. Projects resolved values into new columns on a copy of the row
5. Returns a new list — input is never mutated

Rows already marked `row status="error"` are passed through unchanged.

## API

```python
map_json_to_rows(
    rows,                        # list of row dicts
    json_items,                  # list of JSON object dicts
    mapping,                     # {"output_column": "json.dotted.path"}
    row_key,                     # column name in rows to match on
    json_key,                    # field in json_items to match on
    *,
    on_no_match="skip",          # "skip" | "error" | "blank"
    allow_empty_json=False,      # if True, empty json_items is not an error
) -> list[dict]
```

### `on_no_match`

| Value | Behaviour |
|---|---|
| `"skip"` | Row is returned unchanged — no new columns added |
| `"error"` | `row status="error"`, `message=...`, mapping columns set to `""` |
| `"blank"` | Mapping columns set to `""`, row status untouched |

### Composing with `tha-csv-runner`

```python
from tha_csv_runner import ThaCSV
from tha_map_runner import map_json_to_rows
import requests

runner = ThaCSV()
runner.read("Step 1 of 2", "input.csv", ["Org BK"])

api_response = requests.get(api_url).json()

runner.rows = map_json_to_rows(
    rows=runner.rows,
    json_items=api_response,
    mapping={"Org Name": "name", "District": "parent.sourcedId"},
    row_key="Org BK",
    json_key="sourcedId",
)

runner.write("Step 2 of 2", "output.csv")
```

## License

MIT
