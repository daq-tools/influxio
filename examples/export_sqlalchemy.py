"""
Export data from the InfluxDB API to PostgreSQL/CrateDB.

- Load a synthetic pandas DataFrame into InfluxDB.
- Transfer data from InfluxDB to RDBMS database using SQLAlchemy/pandas/Dask.
- Read back a few samples worth of data from the RDBMS database.
"""

import logging

import sqlalchemy as sa

from influxio.adapter import InfluxDbAdapter
from influxio.io import dataframe_to_sql
from influxio.testdata import DataFrameFactory
from influxio.util.common import jd, setup_logging

logger = logging.getLogger(__name__)

DBURI = "crate://localhost:4200"
DATASET_SIZE = 15_000


def main():
    logger.info("Connecting to InfluxDB")
    influx = InfluxDbAdapter(
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

    # Transfer data.
    logger.info("Transferring data")
    for df in influx.read_df():
        logger.info("Loading data frame into RDBMS/SQL database using pandas/Dask")
        dataframe_to_sql(df, dburi=DBURI, tablename="demo", progress=True)

    # Read back data from target database.
    logger.info("Reading back data from the target database")
    engine = sa.create_engine(DBURI)
    with engine.connect() as connection:
        connection.execute(sa.text("REFRESH TABLE demo;"))
        result = connection.execute(sa.text("SELECT * FROM demo LIMIT 3;"))
        records = [dict(item) for item in result.mappings().fetchall()]
        jd(records)
    logger.info("Ready.")


if __name__ == "__main__":
    setup_logging()
    main()
