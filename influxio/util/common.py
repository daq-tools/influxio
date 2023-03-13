import json
import logging
import sys
import typing as t


def setup_logging(level=logging.INFO):
    log_format = "%(asctime)-15s [%(name)-24s] %(levelname)-8s: %(message)s"
    logging.basicConfig(format=log_format, stream=sys.stderr, level=level)


def get_version(appname):
    from importlib.metadata import PackageNotFoundError, version  # noqa

    try:
        return version(appname)
    except PackageNotFoundError:  # pragma: no cover
        return "unknown"


def jd(data: t.Any):
    """
    Pretty-print JSON with indentation.
    """
    print(json.dumps(data, indent=2))  # noqa: T201
