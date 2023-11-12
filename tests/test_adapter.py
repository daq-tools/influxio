from influxio.model import SqlAlchemyAdapter


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
