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
