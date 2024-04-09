"""
Export data from an InfluxDB data directory to InfluxDB Line Protocol (ILP) format.

- Load a synthetic pandas DataFrame into InfluxDB.
- Export data to InfluxDB line protocol format (ILP).
- Read back a few samples worth of data from the ILP file.

https://docs.influxdata.com/influxdb/latest/reference/syntax/line-protocol/
"""

import gzip
import logging
from pathlib import Path

from influxio.adapter import InfluxDbApiAdapter, InfluxDbEngineAdapter
from influxio.io import dataframe_from_lineprotocol
from influxio.testdata import DataFrameFactory
from influxio.util.common import setup_logging

logger = logging.getLogger(__name__)


LINEPROTOCOL_FILE = Path("./var/export/demo.lp.gz")
DATASET_SIZE = 15_000


def main():
    logger.info("Connecting to InfluxDB")
    influx = InfluxDbApiAdapter(
        url="http://localhost:8086",
        org="example",
        token="token",  # noqa: S106
        bucket="testdrive",
        measurement="demo",
    )

    # Provision data to source database.
    logger.info("Provisioning InfluxDB")
    dff = DataFrameFactory(rows=DATASET_SIZE)
    df = dff.make("dateindex")
    influx.write_df(df)

    # Export data into file using lineprotocol format.
    logger.info("Exporting data to lineprotocol file (ILP)")
    LINEPROTOCOL_FILE.parent.mkdir(parents=True, exist_ok=True)

    source_url = f"file://var/lib/influxdb2/engine?bucket-id={influx.bucket_id}&measurement={influx.measurement}"
    influx_data = InfluxDbEngineAdapter.from_url(source_url)
    influx_data.to_lineprotocol(url=f"file://{LINEPROTOCOL_FILE}")

    logger.info("Reading back data from lineprotocol file")
    with gzip.open(LINEPROTOCOL_FILE) as buffer:
        df = dataframe_from_lineprotocol(buffer)
        print(df)  # noqa: T201

    logger.info("Ready.")


if __name__ == "__main__":
    setup_logging()
    main()
