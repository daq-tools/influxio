import json
import logging
import shlex
import subprocess
import sys
import typing as t
from enum import Enum
from textwrap import dedent

logger = logging.getLogger(__name__)


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


def run_command(command: str):
    """
    https://stackoverflow.com/a/48813330
    """
    command = dedent(command).strip()
    cmd = shlex.split(command)
    logger.info(f"Running command: {command}")
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)  # noqa: S603
    except subprocess.CalledProcessError as exc:
        logger.error(f"Command failed (exit code {exc.returncode}). The command was:\n{command}")
        logger.error(exc.output)
        raise
    else:
        if output:
            logger.info(f"Command output:\n{output}")


class AutoStrEnum(str, Enum):
    """
    StrEnum where enum.auto() returns the field name.
    See https://docs.python.org/3.9/library/enum.html#using-automatic-values

    From https://stackoverflow.com/a/74539097.
    """

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list) -> str:  # noqa: ARG004
        return name
