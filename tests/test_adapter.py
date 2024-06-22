from influxio.adapter import FileAdapter, SqlAlchemyAdapter
from influxio.model import DataFormat


def test_cratedb_adapter_void():
    adapter = SqlAlchemyAdapter.from_url("crate://localhost:4200/")
    assert adapter.database is None
    assert adapter.table is None
    assert adapter.dburi == "crate://localhost:4200"


def test_cratedb_adapter_universal_notation():
    adapter = SqlAlchemyAdapter.from_url("crate://localhost:4200/testdrive/basic")
    assert adapter.database == "testdrive"
    assert adapter.table == "basic"
    assert adapter.dburi == "crate://localhost:4200/?schema=testdrive"


def test_cratedb_adapter_with_ssl():
    adapter = SqlAlchemyAdapter.from_url("crate://localhost:4200/testdrive/basic?ssl=true")
    assert adapter.database == "testdrive"
    assert adapter.table == "basic"
    assert adapter.dburi == "crate://localhost:4200/?schema=testdrive&ssl=true"


def test_cratedb_adapter_table():
    adapter = SqlAlchemyAdapter.from_url("crate://localhost:4200/?table=basic")
    assert adapter.database is None
    assert adapter.table == "basic"
    assert adapter.dburi == "crate://localhost:4200"


def test_cratedb_adapter_schema_table():
    adapter = SqlAlchemyAdapter.from_url("crate://localhost:4200/?schema=testdrive&table=basic")
    assert adapter.database == "testdrive"
    assert adapter.table == "basic"
    assert adapter.dburi == "crate://localhost:4200/?schema=testdrive"


def test_cratedb_adapter_database_table():
    adapter = SqlAlchemyAdapter.from_url("crate://localhost:4200/?database=testdrive&table=basic")
    assert adapter.database == "testdrive"
    assert adapter.table == "basic"
    assert adapter.dburi == "crate://localhost:4200/?schema=testdrive"
    assert adapter.if_exists is None


def test_cratedb_adapter_if_exists():
    adapter = SqlAlchemyAdapter.from_url("crate://localhost:4200/?database=testdrive&table=basic&if-exists=append")
    assert adapter.database == "testdrive"
    assert adapter.table == "basic"
    assert adapter.dburi == "crate://localhost:4200/?schema=testdrive"
    assert adapter.if_exists == "append"


def test_file_adapter_ilp_file():
    adapter = FileAdapter.from_url("file://foo.lp")
    assert adapter.output.path == "foo.lp"
    assert adapter.output.format is DataFormat.LINE_PROTOCOL_UNCOMPRESSED


def test_file_adapter_ilp_stdout():
    adapter = FileAdapter.from_url("file://-?format=lp")
    assert adapter.output.path == "-"
    assert adapter.output.format is DataFormat.LINE_PROTOCOL_UNCOMPRESSED
