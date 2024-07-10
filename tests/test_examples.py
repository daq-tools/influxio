import gzip
import os
import subprocess
import sys
import typing as t
from pathlib import Path

import pytest
import sqlalchemy as sa

from examples.export_lineprotocol import LINEPROTOCOL_FILE
from examples.export_sqlalchemy import DBURI
from influxio.adapter import InfluxDbApiAdapter


def get_example_program_path(filename: str):
    """
    Compute path to example program.
    """
    return Path(__file__).parent.parent.joinpath("examples").joinpath(filename)


def run_program(command: t.List[str]):
    """
    Run a program, connecting stdout and stderr streams with the current ones.
    """
    return subprocess.check_call(  # noqa: S603
        command,
        stdout=sys.stdout.buffer,
        stderr=sys.stderr.buffer,
    )


@pytest.fixture(scope="function", autouse=True)
def reset_resources():
    """
    Make sure each test case function uses a fresh environment.
    """

    # Reset InfluxDB database.
    influx = InfluxDbApiAdapter(
        url="http://localhost:8086",
        org="example",
        token="token",  # noqa: S106
        bucket="testdrive",
        measurement="demo",
    )
    influx.delete_bucket()

    # Reset RDBMS database.
    engine = sa.create_engine(DBURI)
    with engine.connect() as connection:
        connection.execute(sa.text("DROP TABLE IF EXISTS demo;"))

    # Reset export files.
    LINEPROTOCOL_FILE.unlink(missing_ok=True)


@pytest.mark.examples
def test_example_dataframe():
    """
    Verify the `examples/export_sqlalchemy.py` program.
    """

    # Invoke example program.
    example = get_example_program_path("export_sqlalchemy.py")
    exitcode = run_program([sys.executable, example])
    assert exitcode == 0

    # Verify database content.
    engine = sa.create_engine(DBURI)
    with engine.connect() as connection:
        connection.execute(sa.text("REFRESH TABLE demo;"))
        result = connection.execute(sa.text("SELECT COUNT(*) FROM demo;"))
        assert result.fetchone() == (15_000,)


@pytest.mark.examples
def test_example_lineprotocol():
    """
    Verify the `examples/export_lineprotocol.py` program.
    """

    if "CI" in os.environ:
        raise pytest.skip("Needs access to InfluxDB data directory")

    # Invoke example program.
    example = get_example_program_path("export_lineprotocol.py")
    exitcode = run_program([sys.executable, example])
    assert exitcode == 0

    # Verify content of lineprotocol file.
    # Because the example input data contains four columns,
    # there are four times more lines than individual records.
    with gzip.open(LINEPROTOCOL_FILE) as buffer:
        lines = buffer.readlines()
        assert len(lines) == 15_000 * 4
