from pathlib import Path

import influxio.core
from influxio.adapter import SqlAlchemyAdapter


def test_load_lineprotocol_to_sqlite_file(line_protocol_file_basic, caplog):
    """
    Load line protocol file into SQLite.
    """

    # Define source and target URLs.
    source_url = f"file://{line_protocol_file_basic}"
    target_url = "sqlite:///export.sqlite?table=export"

    # Make sure target database is purged.
    Path("export.sqlite").unlink(missing_ok=True)

    # Transfer data.
    influxio.core.copy(source_url, target_url)

    # Verify execution.
    assert f"Copying from {source_url} to {target_url}" in caplog.messages
    assert "Loading line protocol file: tests/testdata/basic.lp" in caplog.messages

    # Verify number of records in target database.
    db = SqlAlchemyAdapter.from_url(target_url)
    records = db.read_records()
    assert len(records) == 2
