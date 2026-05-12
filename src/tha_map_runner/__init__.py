"""tha-map-runner: join JSON responses into CSV-style rows with dotted-path projection."""

from .errors import MapperError
from .mapper import map_json_to_rows

__version__ = "0.1.0"
__all__ = ["MapperError", "map_json_to_rows"]
