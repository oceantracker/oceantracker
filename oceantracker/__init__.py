# ----------- get version number ------------------------------------------------

from importlib.metadata import version

__version__ = version("oceantracker")


# ----------- get release date, stamped into the package at build time -----------

def __getattr__(name):
    # PEP 562 lazy module attribute, avoids importing _build_info/definitions unless asked for
    if name == '__release_date__':
        try:
            from oceantracker._build_info import build_date
            return build_date[:19]
        except ImportError:
            return 'unknown'  # source checkout, no build stamp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
