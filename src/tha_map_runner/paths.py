from typing import Any, TypeAlias, Union

from .errors import MapperError

MappingValue: TypeAlias = Union[str, "dict[str, MappingValue]", "list[str]", "set[str]"]


def include(*paths: str) -> list[str]:
    return list(paths)


def exclude(*keys: str) -> set[str]:
    return set(keys)


def resolve_path(obj: object, path: str) -> object:
    if not path:
        raise ValueError("path must not be empty")
    current: list[object] = [obj]
    for segment in path.split("."):
        nxt: list[object] = []
        for val in current:
            if isinstance(val, dict):
                nxt.append(val.get(segment))
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        nxt.append(item.get(segment))
                    else:
                        nxt.append(None)
            else:
                nxt.append(None)
        flat: list[object] = []
        for v in nxt:
            if isinstance(v, list):
                flat.extend(v)
            else:
                flat.append(v)
        current = flat
    if len(current) == 1:
        return current[0]
    return current


def resolve_mapping_value(match: dict[str, Any], spec: MappingValue) -> object:
    if isinstance(spec, str):
        if spec == "":
            return match
        value = resolve_path(match, spec)
        return "" if value is None else value
    if isinstance(spec, dict):
        return {field: resolve_mapping_value(match, sub) for field, sub in spec.items()}
    if isinstance(spec, list):
        return {path: resolve_mapping_value(match, path) for path in spec}
    if isinstance(spec, set):
        return {k: v for k, v in match.items() if k not in spec}
    raise MapperError(f"invalid mapping value {spec!r}: must be a str, dict, list, or set")
