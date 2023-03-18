import dataclasses

import pytest

import influxio.core
from influxio.model import InfluxAPI


@dataclasses.dataclass
class DatasetItemSpec:
    name: str
    length: int


@pytest.mark.parametrize(
    "spec",
    [
        DatasetItemSpec("dummy", 2),
        DatasetItemSpec("mixed", 20),
        DatasetItemSpec("dateindex", 12),
        DatasetItemSpec("wide", 21),
    ],
    ids=lambda x: x.name,
)
def test_write_testdata(spec: DatasetItemSpec, caplog):
    """
    CLI test: Import test data to InfluxDB.
    """
    dataset = spec.name
    source_url = f"testdata://{dataset}/?rows=3&columns=7"
    target_url = f"http://example:token@localhost:8086/testdrive/testdata-{dataset}"

    # Make sure database is purged.
    api = InfluxAPI.from_url(target_url)
    api.delete()

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Creating data frame" in caplog.messages
    assert f"Importing data frame to InfluxDB. bucket=testdrive, measurement=testdata-{dataset}" in caplog.messages

    # Verify number of records in database.
    records = api.read_records()
    assert len(records) == spec.length


def test_write_lineprotocol(line_protocol_file_basic, caplog):
    """
    CLI test: Import line protocol data to InfluxDB.
    """
    source_url = f"file://{line_protocol_file_basic}"
    target_url = "http://example:token@localhost:8086/testdrive/basic"

    # Make sure database is purged.
    api = InfluxAPI.from_url(target_url)
    api.delete()

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Importing line protocol format to InfluxDB. bucket=testdrive, measurement=basic" in caplog.messages

    # Verify number of records in database.
    records = api.read_records()
    assert len(records) == 2
