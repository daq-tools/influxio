import json
import logging
import sys
import typing as t
from pathlib import Path

import dask.dataframe as dd
import influxdb_client.rest
import pandas as pd
from dask.diagnostics import ProgressBar
from influxdb_client import InfluxDBClient
from yarl import URL

from influxio.util.common import run_command

logger = logging.getLogger(__name__)


class InfluxAPI:
    def __init__(self, url: str, token: str, org: str, bucket: str, measurement: str):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.measurement = measurement
        self.client = InfluxDBClient(url=self.url, org=self.org, token=self.token)

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
        try:
            return self.client.delete_api().delete(
                start="1677-09-21T00:12:43.145224194Z",
                stop="2262-04-11T23:47:16.854775806Z",
                predicate=f'_measurement="{self.measurement}"',
                bucket=self.bucket,
            )
        except influxdb_client.rest.ApiException as ex:
            if ex.status != 404:
                raise

    def read_df(self):
        """ """
        query = f"""
        from(bucket:"{self.bucket}")
            |> range(start: 0, stop: now())
            |> filter(fn: (r) => r._measurement == "{self.measurement}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """
        #
        for df in self.client.query_api().query_data_frame_stream(query=query):
            df = df.drop(["result", "table", "_start", "_stop"], axis=1)
            df = df.rename(columns={"_time": "time", "_measurement": "measurement"})
            yield df

    def read_records(self) -> t.Dict[str, t.Any]:
        query = f"""
            from(bucket: "{self.bucket}")
                |> range(start: 0)
                |> filter(fn: (r) => r._measurement == "{self.measurement}")
            """
        result = self.client.query_api().query(query=query)
        return json.loads(result.to_json())

    def ensure_bucket(self):
        try:
            self.client.buckets_api().create_bucket(bucket_name=self.bucket)
        except influxdb_client.rest.ApiException as ex:
            if ex.status == 422:
                pass
            else:
                raise
        logger.info(f"Bucket id is {self.get_bucket_id()}")

    def write_df(self, df: pd.DataFrame):
        """
        Use batching API to import data frame into InfluxDB.

        https://github.com/influxdata/influxdb-client-python/blob/master/examples/ingest_large_dataframe.py

        TODO: Add precision.
        """
        logger.info(f"Importing data frame to InfluxDB. bucket={self.bucket}, measurement={self.measurement}")
        self.ensure_bucket()
        with self.client.write_api() as write_api:
            write_api.write(
                bucket=self.bucket,
                record=df,
                data_frame_measurement_name=self.measurement,
                # TODO: Add more parameters.
                # write_precision=WritePrecision.MS,
                # data_frame_tag_columns=['tag'],  # noqa: ERA001
            )

    def write_lineprotocol(self, source: t.Union[Path, str], precision: str = "ns"):
        """
        Precision of the timestamps of the lines (default: ns) [$INFLUX_PRECISION]

        The default precision for timestamps is in nanoseconds. If the precision of
        the timestamps is anything other than nanoseconds (ns), you must specify the
        precision in your write request. InfluxDB accepts the following precisions:

            ns - Nanoseconds
            us - Microseconds
            ms - Milliseconds
            s - Seconds

        -- https://docs.influxdata.com/influxdb/cloud/write-data/developer-tools/line-protocol/
        """
        is_url = False
        try:
            URL(source)
            is_url = True
        except:
            pass

        logger.info(f"Importing line protocol format to InfluxDB. bucket={self.bucket}, measurement={self.measurement}")
        self.ensure_bucket()

        if is_url:
            source_option = f'--url="{str(source)}"'
        else:
            source_option = f'--file="{str(source)}"'
        command = f"""
        influx write \
            --token="{self.token}" \
            --org="{self.org}" \
            --bucket="{self.bucket}" \
            --precision={precision} \
            --format=lp \
            {source_option}
        """
        # print("command:", command)
        run_command(command)

    def get_bucket_id(self):
        """
        Resolve bucket name to bucket id.
        """
        bucket: influxdb_client.Bucket = self.client.buckets_api().find_bucket_by_name(bucket_name=self.bucket)
        if bucket is None:
            raise KeyError(f"Bucket not found: {self.bucket}")
        return bucket.id

    def to_lineprotocol(self, engine_path: str, output_path: str):
        """
        https://docs.influxdata.com/influxdb/v2.6/migrate-data/migrate-oss/

        :return:
        """
        logger.info("Exporting data to InfluxDB line protocol format (ILP)")
        bucket_id = self.get_bucket_id()
        command = f"""
        influxd inspect export-lp \
            --engine-path {engine_path} \
            --bucket-id '{bucket_id}' \
            --measurement '{self.measurement}' \
            --output-path '{output_path}' \
            --compress
        """
        run_command(command)

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
