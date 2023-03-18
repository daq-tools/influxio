import io
from pathlib import Path

import pytest


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
def line_protocol_url_basic():
    return "https://raw.githubusercontent.com/daq-tools/influxio/main/tests/testdata/basic.lp"


@pytest.fixture
def line_protocol_file_irregular():
    return Path("tests/testdata/air-sensor-data-irregular.lp")
