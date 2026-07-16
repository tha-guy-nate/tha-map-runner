"""tha-map-runner: join JSON responses into CSV-style rows with dotted-path projection."""

from .errors import MapperError
from .mapper import ThaMap
from .paths import exclude, include

__version__ = "0.3.0"
__all__ = ["MapperError", "ThaMap", "exclude", "include"]
