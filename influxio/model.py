import logging
import shlex
import subprocess

import dask.dataframe as dd
import influxdb_client.rest
import pandas as pd
from dask.diagnostics import ProgressBar
from influxdb_client import InfluxDBClient
from yarl import URL

logger = logging.getLogger(__name__)


class InfluxAPI:
    def __init__(self, url: str, token: str, org: str, bucket: str, measurement: str):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.measurement = measurement

    @classmethod
    def from_url(cls, url: t.Union[URL, str]) -> "InfluxAPI":
        if isinstance(url, str):
            url: URL = URL(url)
        token = url.password
        org = url.user
        bucket, measurement = url.path.strip("/").split("/")
        bare_url = f"{url.scheme}://{url.host}:{url.port}"
        return cls(url=bare_url, token=token, org=org, bucket=bucket, measurement=measurement)

    def delete(self):
        with InfluxDBClient(url=self.url, org=self.org, token=self.token) as client:
            return client.delete_api().delete(
                start="1677-09-21T00:12:43.145224194Z",
                stop="2262-04-11T23:47:16.854775806Z",
                predicate=f'_measurement="{self.measurement}"',
                bucket=self.bucket,
            )

    def read_df(self):
        """ """
        query = f"""
        from(bucket:"{self.bucket}")
            |> range(start: -30y, stop: now())
            |> filter(fn: (r) => r._measurement == "{self.measurement}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """
        #
        with InfluxDBClient(url=self.url, org=self.org, token=self.token) as client:
            for df in client.query_api().query_data_frame_stream(query=query):
                df = df.drop(["result", "table", "_start", "_stop"], axis=1)
                df = df.rename(columns={"_time": "time", "_measurement": "measurement"})
                yield df

    def write_df(self, df: pd.DataFrame):
        """
        Use batching API to import data frame into InfluxDB.

        https://github.com/influxdata/influxdb-client-python/blob/master/examples/ingest_large_dataframe.py
        """
        logger.info(f"Importing data frame to InfluxDB. bucket={self.bucket}, measurement={self.measurement}")
        with InfluxDBClient(url=self.url, org=self.org, token=self.token) as client:
            try:
                client.buckets_api().create_bucket(bucket_name=self.bucket)
            except influxdb_client.rest.ApiException as ex:
                if ex.status == 422:
                    pass
                else:
                    raise
            logger.info(f"Bucket id is {self.get_bucket_id()}")
            with client.write_api() as write_api:
                write_api.write(
                    bucket=self.bucket,
                    record=df,
                    data_frame_measurement_name=self.measurement,
                    # data_frame_tag_columns=['tag'],  # noqa: ERA001
                )

    def get_bucket_id(self):
        """
        Resolve bucket name to bucket id.
        """
        with InfluxDBClient(url=self.url, org=self.org, token=self.token) as client:
            bucket: influxdb_client.Bucket = client.buckets_api().find_bucket_by_name(bucket_name=self.bucket)
            if bucket is None:
                raise KeyError(f"Bucket not found: {self.bucket}")
            return bucket.id

    def to_lineprotocol(self, engine_path: str, output_path: str):
        """
        https://docs.influxdata.com/influxdb/v2.6/migrate-data/migrate-oss/

        :return:
        """
        logger.info("Exporting data to InfluxDB lineprotocol format (ILP)")
        bucket_id = self.get_bucket_id()
        command = f"""
        influxd inspect export-lp \
            --engine-path {engine_path} \
            --bucket-id '{bucket_id}' \
            --measurement '{self.measurement}' \
            --output-path '{output_path}' \
            --compress
        """
        subprocess.check_output(shlex.split(command.strip()), stderr=subprocess.STDOUT)

    def df_to_sql(self, df: pd.DataFrame):
        """
        https://stackoverflow.com/questions/62404502/using-dasks-new-to-sql-for-improved-efficiency-memory-speed-or-alternative-to
        """
        logger.info("Importing data frame to CrateDB")
        pbar = ProgressBar()
        pbar.register()

        # TODO: Make variable configurable.
        #       Default to nproc / 2?
        ddf = dd.from_pandas(df, npartitions=4)

        # TODO: Make configurable.
        dburi = "crate://localhost:4200"
        # dburi = "crate+psycopg://localhost:4200"  # noqa: ERA001

        # NOTE: `chunksize` is important, otherwise CrateDB will croak with
        #       RuntimeException[java.lang.OutOfMemoryError: Java heap space]
        # TODO: Unlock `engine_kwargs={"fast_executemany": True}`.
        #       Exception:
        #           TypeError: Invalid argument(s) 'fast_executemany' sent to create_engine(),
        #           using configuration CrateDialect/QueuePool/Engine.
        #           Please check that the keyword arguments are appropriate for this combination of components.
        #       Note that `fast_executemany` is only provided by `pyodbc`.
        # TODO: Unlock `method="multi"`
        #       sqlalchemy.exc.CompileError: The 'crate' dialect with current
        #       database version settings does not support in-place multirow inserts.
        ddf.to_sql("demo", uri=dburi, index=False, if_exists="replace", chunksize=10000, parallel=True)

        # TODO: Read back and `assert_frame_equal()`
