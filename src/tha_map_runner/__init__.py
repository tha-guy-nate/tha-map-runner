"""tha-map-runner: join JSON responses into CSV-style rows with dotted-path projection."""

from .errors import MapperError
from .mapper import enrich_rows

__version__ = "0.1.0"
__all__ = ["MapperError", "enrich_rows"]
