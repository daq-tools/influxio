import os
from pathlib import Path

import pytest
import urllib3
from yarl import URL

import influxio.core
from influxio.adapter import SqlAlchemyAdapter
from tests.conftest import CRATEDB_URL, INFLUXDB_API_URL

INFLUXDB_ENGINE_URL = "file://var/lib/influxdb2/engine?bucket-id={bucket_id}&measurement={measurement}"
POSTGRESQL_URL = "postgresql+psycopg2://postgres@localhost:5432/testdrive/basic"
ILP_URL_STDOUT = "file://-?format=lp"


@pytest.fixture
def sqlite_url(tmp_path) -> str:
    dbpath = tmp_path / "basic.sqlite"
    return f"sqlite:///{dbpath}?table=basic"


@pytest.fixture
def sqlite(sqlite_url) -> SqlAlchemyAdapter:
    return SqlAlchemyAdapter.from_url(sqlite_url)


@pytest.fixture
def postgresql() -> SqlAlchemyAdapter:
    adapter = SqlAlchemyAdapter.from_url(POSTGRESQL_URL)
    adapter.create_database()
    adapter.run_sql("DROP TABLE IF EXISTS basic")
    return adapter


@pytest.fixture
def ilp_url_file(tmp_path) -> URL:
    ilppath = tmp_path / "basic.lp"
    return URL(f"file://{ilppath}")


@pytest.fixture
def provision_influxdb(influxdb, line_protocol_file_basic):
    """
    Provision seed data to InfluxDB.
    """
    source_url = f"file://{line_protocol_file_basic}"
    target_url = INFLUXDB_API_URL

    # Transfer data.
    influxio.core.copy(source_url, target_url)


def test_export_cratedb_default(caplog, influxdb, provision_influxdb, cratedb):
    """
    Export data from InfluxDB to CrateDB, happy path.
    """

    source_url = INFLUXDB_API_URL
    target_url = CRATEDB_URL

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Loading dataframes into RDBMS/SQL database using pandas/Dask" in caplog.messages

    # Verify number of records in target database.
    cratedb.refresh_table()
    records = cratedb.read_records()
    assert len(records) == 2


def test_export_cratedb_no_data(caplog, influxdb, provision_influxdb, cratedb):
    """
    Export data from InfluxDB to CrateDB, but not data exists at source.
    """

    source_url = INFLUXDB_API_URL + "_unknown"
    target_url = CRATEDB_URL

    # Transfer data.
    with pytest.raises(IOError) as exc:
        influxio.core.copy(source_url, target_url)

    assert exc.match("No data has been loaded from InfluxDB")

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Loading dataframes into RDBMS/SQL database using pandas/Dask" in caplog.messages
    assert "No data has been loaded from InfluxDB" in caplog.messages

    # Verify number of records in target database.
    cratedb.refresh_table()
    records = cratedb.read_records()
    assert len(records) == 0


def test_export_cratedb_fail_if_target_exists(caplog, influxdb, provision_influxdb, cratedb):
    """
    Exporting data from InfluxDB to CrateDB should fail if target table exists.
    """

    source_url = INFLUXDB_API_URL
    target_url = CRATEDB_URL

    # Create a table that will cause the export process to fail.
    cratedb.run_sql("CREATE TABLE basic (foo INT)")

    # Transfer data.
    with pytest.raises(ValueError) as ex:
        influxio.core.copy(source_url, target_url)
    ex.match("Table 'basic' already exists.")


def test_export_cratedb_if_exists_unknown(caplog, influxdb, provision_influxdb, cratedb):
    """
    Exporting data from InfluxDB to CrateDB should fail if target table exists.
    """

    source_url = INFLUXDB_API_URL
    target_url = CRATEDB_URL + "?if-exists=Hotzenplotz"

    # Create a table that will cause the export process to fail.
    cratedb.run_sql("CREATE TABLE basic (foo INT)")

    # Transfer data.
    with pytest.raises(ValueError) as ex:
        influxio.core.copy(source_url, target_url)
    ex.match("'Hotzenplotz' is not valid for if_exists")


def test_export_cratedb_if_exists_replace(caplog, influxdb, provision_influxdb, cratedb):
    """
    Exporting data from InfluxDB to CrateDB will succeed with ``if-exists=replace``.
    """

    source_url = INFLUXDB_API_URL
    target_url = CRATEDB_URL + "?if-exists=replace"

    # Create a table that would cause the export process to fail.
    cratedb.run_sql("CREATE TABLE basic (foo INT)")

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify number of records in target database.
    cratedb.refresh_table()
    records = cratedb.read_records()
    assert len(records) == 2


def test_export_cratedb_if_exists_append(caplog, influxdb, provision_influxdb, cratedb):
    """
    Exporting data from InfluxDB to CrateDB twice will succeed with ``if-exists=append``.
    """

    source_url = INFLUXDB_API_URL
    target_url = CRATEDB_URL + "?if-exists=append"

    # Transfer data.
    influxio.core.copy(source_url, target_url)
    influxio.core.copy(source_url, target_url)

    # Verify number of records in target database.
    cratedb.refresh_table()
    records = cratedb.read_records()
    assert len(records) == 4


def test_export_postgresql(caplog, influxdb, provision_influxdb, postgresql):
    """
    Export data from InfluxDB to PostgreSQL.
    """

    source_url = INFLUXDB_API_URL
    target_url = POSTGRESQL_URL

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Loading dataframes into RDBMS/SQL database using pandas/Dask" in caplog.messages

    # Verify number of records in target database.
    records = postgresql.read_records()
    assert len(records) == 2


def test_export_sqlite(caplog, influxdb, provision_influxdb, sqlite, sqlite_url):
    """
    Export data from InfluxDB to SQLite.
    """

    source_url = INFLUXDB_API_URL
    target_url = sqlite_url

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Loading dataframes into RDBMS/SQL database using pandas/Dask" in caplog.messages

    # Verify number of records in target database.
    records = sqlite.read_records()
    assert len(records) == 2


def test_export_api_ilp_stdout(caplog, capsys, influxdb, provision_influxdb):
    """
    Verify exporting data from InfluxDB API to lineprotocol format (ILP) on STDOUT.
    """

    source_url = INFLUXDB_API_URL
    target_url = ILP_URL_STDOUT

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Exporting dataframes in LINE_PROTOCOL_UNCOMPRESSED format to -" in caplog.messages

    # Verify records on stdout have the right shape.
    out, err = capsys.readouterr()
    assert (
        out
        == r"""
basic,fruits=apple\,banana,id=1,name=foo price=0.42 1414747376000000000
basic,fruits=pear,id=2,name=bar price=0.84 1414747378000000000
""".lstrip()
    )


def test_export_api_ilp_file(caplog, capsys, influxdb, provision_influxdb, ilp_url_file):
    """
    Verify exporting data from InfluxDB API to lineprotocol format (ILP) into file.
    """

    source_url = INFLUXDB_API_URL
    target_url = str(ilp_url_file)

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert f"Exporting dataframes in LINE_PROTOCOL_UNCOMPRESSED format to {ilp_url_file.path}" in caplog.messages

    # Verify records in file have the right shape.
    out = Path(ilp_url_file.path).read_text()
    assert (
        out
        == r"""
basic,fruits=apple\,banana,id=1,name=foo price=0.42 1414747376000000000
basic,fruits=pear,id=2,name=bar price=0.84 1414747378000000000
""".lstrip()
    )


def test_export_api_ilp_timeout(caplog, capsys, influxdb, provision_influxdb):
    """
    Verify that the `timeout` option works.
    """

    source_url = INFLUXDB_API_URL + "?timeout=0.001"
    target_url = ILP_URL_STDOUT

    # Transfer data.
    with pytest.raises(urllib3.exceptions.ReadTimeoutError) as ex:
        influxio.core.copy(source_url, target_url)
    assert ex.match("Read timed out.")


def test_export_directory_ilp_stdout(caplog, capsys, influxdb, provision_influxdb):
    """
    Verify exporting data from InfluxDB data directory to lineprotocol format (ILP) on STDOUT.
    """

    if "CI" in os.environ:
        raise pytest.skip("Needs access to InfluxDB data directory")

    source_url = INFLUXDB_ENGINE_URL.format(
        bucket_id=influxdb.bucket_id,
        measurement=influxdb.measurement,
    )
    target_url = ILP_URL_STDOUT

    # Transfer data.
    result = influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert (
        "Exporting data to InfluxDB line protocol format (ILP): DataFormat.LINE_PROTOCOL_UNCOMPRESSED"
        in caplog.messages
    )

    # Verify records on stdout have the right shape.
    out, err = capsys.readouterr()

    assert "exporting TSM files" in result.stderr
    assert "exporting WAL files" in result.stderr
    assert "export complete" in result.stderr

    # Full message:
    # detected deletes in WAL file, some deleted data may be brought back by replaying this export
    # assert "detected deletes in WAL file" in result.stderr

    assert "basic,fruits=pear,id=2,name=bar price=0.84 1414747378000000000" in out
    assert r"basic,fruits=apple\,banana,id=1,name=foo price=0.42 1414747376000000000" in out


def test_export_directory_ilp_file(caplog, capsys, influxdb, provision_influxdb, ilp_url_file):
    """
    Verify exporting data from InfluxDB data directory to lineprotocol format (ILP) into file.
    """

    if "CI" in os.environ:
        raise pytest.skip("Needs access to InfluxDB data directory")

    source_url = INFLUXDB_ENGINE_URL.format(
        bucket_id=influxdb.bucket_id,
        measurement=influxdb.measurement,
    )
    target_url = ilp_url_file

    # Transfer data.
    result = influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert (
        "Exporting data to InfluxDB line protocol format (ILP): DataFormat.LINE_PROTOCOL_UNCOMPRESSED"
        in caplog.messages
    )

    assert "exporting TSM files" in result.stderr
    assert "exporting WAL files" in result.stderr
    assert "export complete" in result.stderr

    # Verify records in output file have the right shape.
    out = Path(ilp_url_file.path).read_text()
    assert "basic,fruits=pear,id=2,name=bar price=0.84 1414747378000000000" in out
    assert r"basic,fruits=apple\,banana,id=1,name=foo price=0.42 1414747376000000000" in out


def test_export_directory_fail_wrong_path(tmp_path):

    if "CI" in os.environ:
        raise pytest.skip("Needs access to InfluxDB data directory")

    with pytest.raises(FileNotFoundError) as ex:
        influxio.core.copy(f"file://{tmp_path}", ILP_URL_STDOUT)
    assert ex.match(f"No InfluxDB data directory: {tmp_path}")


def test_export_directory_fail_bucket_id_missing():

    if "CI" in os.environ:
        raise pytest.skip("Needs access to InfluxDB data directory")

    with pytest.raises(ValueError) as ex:
        influxio.core.copy("file://var/lib/influxdb2/engine", ILP_URL_STDOUT)
    assert ex.match("Parameter missing or empty: bucket-id")


def test_export_directory_fail_measurement_missing():

    if "CI" in os.environ:
        raise pytest.skip("Needs access to InfluxDB data directory")

    with pytest.raises(ValueError) as ex:
        influxio.core.copy("file://var/lib/influxdb2/engine?bucket-id=fc6bb114ceb3ac0b", ILP_URL_STDOUT)
    assert ex.match("Parameter missing or empty: measurement")
