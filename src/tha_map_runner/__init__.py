"""tha-map-runner: join JSON responses into CSV-style rows with dotted-path projection."""

from .errors import MapperError
from .mapper import ThaMap

__version__ = "0.2.4"
__all__ = ["MapperError", "ThaMap"]
