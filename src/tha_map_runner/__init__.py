"""tha-map-runner: join JSON responses into CSV-style rows with dotted-path projection."""

from importlib.metadata import version

from .errors import MapperError
from .mapper import ThaMap
from .paths import exclude, include

__version__ = version("tha-map-runner")
__all__ = ["MapperError", "ThaMap", "exclude", "include"]
