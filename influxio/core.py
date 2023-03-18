import logging
from pathlib import Path

from yarl import URL

from influxio.model import InfluxAPI
from influxio.testdata import DataFrameFactory

logger = logging.getLogger(__name__)


def copy(source: str, target: str):
    """
    Copy/transfer data from/to InfluxDB API / InfluxDB line protocol / RDBMS.

    RDBMS is any SQLAlchemy-supported database.

    `source` and `target` are resource identifiers in URL format.

    When the InfluxDB API is addressed, the schema is:
    http://example:token@localhost:8086/testdrive/demo

    This means:
    - Organization: example
    - Authentication: token
    - Bucket: testdrive
    - Measurement: demo
    """
    source = URL(source)
    target = URL(target)

    logger.info(f"Copying from {source} to {target}")

    if target.scheme.startswith("http"):
        sink = InfluxAPI.from_url(target)
    else:
        raise NotImplementedError(f"Data sink not implemented: {target}")

    if source.scheme == "testdata":
        dff = DataFrameFactory(**source.query)
        df = dff.make(source.host)
        sink.write_df(df)

    elif source.scheme == "file":
        path = Path(source.host).joinpath(Path(source.path).relative_to("/"))
        # TODO: Determine file type by suffix.
        # TODO: Make `precision` configurable.
        sink.write_lineprotocol(path)

    elif source.scheme.startswith("http"):
        sink.write_lineprotocol(str(source))

    else:
        raise NotImplementedError(f"Data source not implemented: {source}")
