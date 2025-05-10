from __future__ import annotations

import logging
import os
from pathlib import Path

from ucumvert.parser import (
    get_ucum_parser,
    update_lark_ucum_grammar_file,
)
from ucumvert.ucum_pint import (
    PintUcumRegistry,
    UcumToPintStrTransformer,
    UcumToPintTransformer,
    ucum_preprocessor,
)

try:
    from ucumvert._version import __version__, __version_tuple__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0"
    __version_tuple__ = (0, 0, 0)

try:  # pragma: no cover
    import pydot  # noqa: F401

    HAS_PYDOT = True
except ImportError:  # pragma: no cover
    HAS_PYDOT = False

__all__ = [
    "PintUcumRegistry",
    "UcumToPintStrTransformer",
    "UcumToPintTransformer",
    "get_ucum_parser",
    "ucum_preprocessor",
    "update_lark_ucum_grammar_file",
]

# Note that nothing is passed to getLogger to set the "root" logger
logger = logging.getLogger()


def setup_logging(loglevel: int = logging.INFO, logfile: Path | None = None) -> None:
    """
    Setup logging to console and optionally a file.

    The default loglevel is INFO.
    """
    loglevel_name = os.getenv("LOGLEVEL", "").strip().upper()
    if loglevel_name in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        loglevel = getattr(logging, loglevel_name, logging.INFO)

    # Apply constraints. CRITICAL=FATAL=50 is the maximum, NOTSET=0 the minimum.
    loglevel = min(logging.FATAL, max(loglevel, logging.NOTSET))

    # Setup handler for logging to console
    logging.basicConfig(level=loglevel, format="%(levelname)-8s|%(message)s")

    if logfile is not None:  # pragma: no cover
        # Setup handler for logging to file
        fh = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=100000, backupCount=5
        )
        fh.setLevel(loglevel)
        fh_formatter = logging.Formatter(
            fmt="%(asctime)s|%(name)-20s|%(levelname)-8s|%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)
