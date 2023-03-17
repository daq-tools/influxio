import dataclasses

import pytest
from click.testing import CliRunner

from influxio.cli import cli
from influxio.model import InfluxAPI


def test_info():
    """
    CLI test: Invoke `influxio info`
    """
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="info",
        catch_exceptions=False,
    )
    assert result.exit_code == 0


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
    target_url = f"http://example:token@localhost:8086/testdrive/testdata-{dataset}"

    api = InfluxAPI.from_url(target_url)
    api.delete()

    runner = CliRunner()

    result = runner.invoke(
        cli,
        args=f"copy testdata://{dataset}/?rows=3&columns=7 {target_url}",
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Verify execution.
    assert f"Copying from testdata://{dataset}/?rows=3&columns=7 to {target_url}" in caplog.messages
    assert "Creating data frame" in caplog.messages
    assert f"Importing data frame to InfluxDB. bucket=testdrive, measurement=testdata-{dataset}" in caplog.messages
    assert "Ready." in caplog.messages

    # Verify number of records in database.
    records = api.read_records()
    assert len(records) == spec.length
