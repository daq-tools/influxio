from click.testing import CliRunner

from influxio.cli import cli


def test_testdata(caplog):
    """
    CLI test: Import test data to InfluxDB.
    """
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="copy testdata://dateindex http://example:token@localhost:8086/testdrive/demo",
        catch_exceptions=False,
    )

    assert result.exit_code == 0

    assert "Copying from testdata://dateindex to http://example:token@localhost:8086/testdrive/demo" in caplog.messages
    assert "Creating data frame" in caplog.messages
    assert "Importing data frame to InfluxDB. bucket=testdrive, measurement=demo" in caplog.messages
    assert "Ready." in caplog.messages
