import logging
import typing as t
from pathlib import Path

from yarl import URL

from influxio.adapter import FileAdapter, InfluxDbApiAdapter, InfluxDbEngineAdapter, SqlAlchemyAdapter
from influxio.model import CommandResult
from influxio.util.db import get_sqlalchemy_dialects

logger = logging.getLogger(__name__)


def copy(source: str, target: str, progress: bool = False) -> t.Union[CommandResult, None]:
    """
    Copy/transfer data from/to InfluxDB API / InfluxDB line protocol / RDBMS.

    RDBMS is any SQLAlchemy-supported database.

    `source` and `target` are resource identifiers in URL format.

    When InfluxDB is addressed, the schema is:
    http://example:token@localhost:8086/testdrive/demo

    This means:
    - Organization: example
    - Authentication: token
    - Bucket: testdrive
    - Measurement: demo

    When an RDBMS is addressed through SQLAlchemy, the schema is:
    http://username:password@localhost:12345/testdrive/demo

    This means:
    - Database or schema: testdrive
    - Table name: demo
    """
    source_url = URL(source)
    target_url = URL(target)

    sqlalchemy_dialects = get_sqlalchemy_dialects()

    logger.info(f"Copying from {source} to {target}")

    scheme_primary = target_url.scheme.split("+")[0]

    if target_url.scheme.startswith("http"):
        sink = InfluxDbApiAdapter.from_url(target)
    elif scheme_primary in sqlalchemy_dialects:
        sink = SqlAlchemyAdapter.from_url(target, progress=True)
    elif target_url.scheme == "file":
        sink = FileAdapter.from_url(target, progress=True)
    else:
        raise NotImplementedError(f"Data sink not implemented: {target_url}")

    if source_url.scheme == "testdata":
        from influxio.testdata import DataFrameFactory

        dff = DataFrameFactory(**source_url.query)
        df = dff.make(source_url.host)
        sink.write_df(df)

    elif source_url.scheme == "file":

        # Export
        if target_url.scheme == "file":
            path = source_url.host + source_url.path
            source_path_dir = [path.name for path in Path(path).iterdir()]
            if "data" in source_path_dir and "wal" in source_path_dir:
                source_element = InfluxDbEngineAdapter.from_url(source)
                return source_element.to_lineprotocol(url=target_url)
            else:
                raise NotImplementedError(f"Data source not implemented: {source_url}")

        # Import
        else:
            path = Path(source_url.host).joinpath(Path(source_url.path).relative_to("/"))
            # TODO: Determine file type by suffix.
            # TODO: Make `precision` configurable.
            sink.from_lineprotocol(path)

    elif source_url.scheme.startswith("http"):
        if isinstance(sink, (FileAdapter, SqlAlchemyAdapter)):
            source_node = InfluxDbApiAdapter.from_url(source)
            sink.write(source_node)
        else:
            sink.from_lineprotocol(str(source_url))

    else:
        raise NotImplementedError(f"Data source not implemented: {source_url}")

    return None
