import logging

from yarl import URL

from influxio.model import InfluxAPI
from influxio.testdata import DataFrameFactory

logger = logging.getLogger(__name__)


def copy(source: str, target: str):
    """
    Copy/transfer data from/to InfluxDB API / InfluxDB line protocol / RDBMS.

    RDBMS is any SQLAlchemy-supported database.
    """
    source = URL(source)
    target = URL(target)

    logger.info(f"Copying from {source} to {target}")

    if source.scheme == "testdata":
        dff = DataFrameFactory()
        df = dff.make(source.host)
    else:
        raise NotImplementedError(f"Data source not implemented: {source}")

    if target.scheme == "http":
        # http://example:token@localhost:8086/testdrive/demo
        url = f"{target.scheme}://{target.host}:{target.port}"
        token = target.password
        org = target.user
        bucket, measurement = target.path.strip("/").split("/")
        api = InfluxAPI(url=url, token=token, org=org, bucket=bucket, measurement=measurement)
        api.write_df(df)
    else:
        raise NotImplementedError(f"Data sink not implemented: {target}")
