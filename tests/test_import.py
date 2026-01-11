import dataclasses

import pytest

import influxio.core
from influxio.adapter import InfluxDbApiAdapter


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
def test_import_testdata(spec: DatasetItemSpec, caplog):
    """
    CLI test: Import test data to InfluxDB.
    """
    dataset = spec.name
    source_url = f"testdata://{dataset}/?rows=3&columns=7"
    target_url = f"http://example:token@localhost:8086/testdrive/testdata-{dataset}"

    # Make sure database is purged.
    api = InfluxDbApiAdapter.from_url(target_url)
    api.delete_measurement()

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Creating data frame" in caplog.messages
    assert f"Importing data frame to InfluxDB. bucket=testdrive, measurement=testdata-{dataset}" in caplog.messages

    # Verify number of records in database.
    records = api.read_records()
    assert len(records) == spec.length


def test_import_lineprotocol_file_basic(line_protocol_file_basic, caplog):
    """
    CLI test: Import line protocol data to InfluxDB. Single measurement.
    """
    source_url = f"file://{line_protocol_file_basic}"
    target_url = "http://example:token@localhost:8086/testdrive/basic"

    # Make sure database is purged.
    api = InfluxDbApiAdapter.from_url(target_url)
    api.delete_measurement()

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Importing line protocol format to InfluxDB. bucket=testdrive" in caplog.messages

    # Verify number of records in database.
    records = api.read_records()
    assert len(records) == 2


def test_import_lineprotocol_file_industrial(line_protocol_file_industrial, caplog):
    """
    CLI test: Import line protocol data to InfluxDB. Multiple measurements.
    """
    source_url = f"file://{line_protocol_file_industrial}"
    target_url = "http://example:token@localhost:8086/testdrive"

    # Make sure database is purged.
    api = InfluxDbApiAdapter.from_url(target_url)
    api.delete_measurement()

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Importing line protocol format to InfluxDB. bucket=testdrive" in caplog.messages

    # Verify number of records in database.
    records = api.read_records(measurement="Füllstände")
    assert len(records) == 4
    records = api.read_records(measurement="Gasanalyse")
    assert len(records) == 2
    records = api.read_records(measurement="Stromproduktion")
    assert len(records) == 2


def test_import_lineprotocol_file_irregular(influxdb, cratedb, line_protocol_file_irregular, caplog):
    """
    CLI test: Import line protocol data to InfluxDB, then CrateDB.

    This test is to verify a dataset that progressively includes new tags
    while processing, so the data sink must accompany a dynamic behaviour.
    """

    # Transfer data to InfluxDB.
    source_url = f"file://{line_protocol_file_irregular}"
    target_url = "http://example:token@localhost:8086/testdrive"
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages

    # Transfer data to CrateDB.
    source_url = target_url
    target_url = "crate://crate@localhost:4200/testdrive/basic"
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages

    # Verify number of records in database.
    cratedb.refresh_table()
    records = cratedb.read_records("testdrive.basic")
    assert len(records) == 7


def test_import_lineprotocol_url(line_protocol_url_basic, caplog):
    """
    CLI test: Import line protocol data to InfluxDB.
    """
    source_url = line_protocol_url_basic
    target_url = "http://example:token@localhost:8086/testdrive/basic"

    # Make sure database is purged.
    api = InfluxDbApiAdapter.from_url(target_url)
    api.delete_bucket()

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Importing line protocol format to InfluxDB. bucket=testdrive" in caplog.messages

    # Verify number of records in database.
    records = api.read_records()
    assert len(records) == 2
