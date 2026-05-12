def resolve_path(obj: object, path: str) -> object:
    if not path:
        raise ValueError("path must not be empty")
    for segment in path.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(segment)
    return obj
