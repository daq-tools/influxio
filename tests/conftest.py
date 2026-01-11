import io
from pathlib import Path

import pytest

from influxio.adapter import InfluxDbApiAdapter, SqlAlchemyAdapter

CRATEDB_URL = "crate://crate@localhost:4200/testdrive/basic"
INFLUXDB_API_URL = "http://example:token@localhost:8086/testdrive/basic"


@pytest.fixture
def influxdb() -> InfluxDbApiAdapter:
    adapter = InfluxDbApiAdapter.from_url(INFLUXDB_API_URL)
    adapter.delete_bucket(missing_ok=True)
    return adapter


@pytest.fixture
def cratedb() -> SqlAlchemyAdapter:
    adapter = SqlAlchemyAdapter.from_url(CRATEDB_URL)
    adapter.run_sql("DROP TABLE IF EXISTS basic")
    return adapter


@pytest.fixture
def line_protocol_stream_basic():
    """
    A stream of input data. Here, in InfluxDB line protocol (ILP) format.
    """
    return io.StringIO(
        """
basic,id=1,name=foo,fruits=apple\\,banana price=0.42 1414747376000000000
basic,id=2,name=bar,fruits=pear price=0.84 1414747378000000000
    """.strip()
    )


@pytest.fixture
def line_protocol_file_basic():
    return Path("tests/testdata/basic.lp")


@pytest.fixture
def line_protocol_file_industrial():
    return Path("tests/testdata/industrial.lp")


@pytest.fixture
def line_protocol_url_basic():
    return "https://github.com/daq-tools/influxio/raw/main/tests/testdata/basic.lp"


@pytest.fixture
def line_protocol_file_irregular():
    return Path("tests/testdata/air-sensor-data-irregular.lp")
