from pathlib import Path

import pytest
from yarl import URL

import influxio.core
from influxio.model import InfluxDbAdapter, SqlAlchemyAdapter

CRATEDB_URL = "crate://crate@localhost:4200/testdrive/basic"
INFLUXDB_URL = "http://example:token@localhost:8086/testdrive/basic"
POSTGRESQL_URL = "postgresql+psycopg2://postgres@localhost:5432/testdrive/basic"
ILP_URL_STDOUT = "file://-?format=lp"


@pytest.fixture
def influxdb() -> InfluxDbAdapter:
    return InfluxDbAdapter.from_url(INFLUXDB_URL)


@pytest.fixture
def cratedb() -> SqlAlchemyAdapter:
    return SqlAlchemyAdapter.from_url(CRATEDB_URL)


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
    target_url = INFLUXDB_URL

    # Make sure database is purged.
    influxdb.delete_measurement()

    # Transfer data.
    influxio.core.copy(source_url, target_url)


def test_export_cratedb(caplog, influxdb, provision_influxdb, cratedb):
    """
    Export data from InfluxDB to CrateDB.
    """

    source_url = INFLUXDB_URL
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


def test_export_postgresql(caplog, influxdb, provision_influxdb, postgresql):
    """
    Export data from InfluxDB to PostgreSQL.
    """

    source_url = INFLUXDB_URL
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

    source_url = INFLUXDB_URL
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

    source_url = INFLUXDB_URL
    target_url = ILP_URL_STDOUT

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Exporting dataframes in LINE_PROTOCOL format to -" in caplog.messages

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

    source_url = INFLUXDB_URL
    target_url = str(ilp_url_file)

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert f"Exporting dataframes in LINE_PROTOCOL format to {ilp_url_file.path}" in caplog.messages

    # Verify records in file have the right shape.
    out = Path(ilp_url_file.path).read_text()
    assert (
        out
        == r"""
basic,fruits=apple\,banana,id=1,name=foo price=0.42 1414747376000000000
basic,fruits=pear,id=2,name=bar price=0.84 1414747378000000000
""".lstrip()
    )
