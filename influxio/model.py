import json
import logging
import typing as t
from pathlib import Path

import influxdb_client.rest
import pandas as pd
import psycopg2
import sqlalchemy
import sqlalchemy as sa
from influxdb_client import InfluxDBClient
from sqlalchemy_utils import create_database
from yarl import URL

from influxio.io import dataframe_to_sql
from influxio.util.common import run_command

logger = logging.getLogger(__name__)


class InfluxDbAdapter:
    def __init__(self, url: str, token: str, org: str, bucket: str, measurement: str, debug: bool = False):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.measurement = measurement
        self.debug = debug
        self.client = InfluxDBClient(url=self.url, org=self.org, token=self.token, debug=self.debug)

    @classmethod
    def from_url(cls, url: t.Union[URL, str], **kwargs) -> "InfluxDbAdapter":
        if isinstance(url, str):
            url: URL = URL(url)
        token = url.password
        org = url.user
        bucket, measurement = url.path.strip("/").split("/")
        bare_url = f"{url.scheme}://{url.host}:{url.port}"
        return cls(url=bare_url, token=token, org=org, bucket=bucket, measurement=measurement, **kwargs)

    def delete_measurement(self):
        """
        https://docs.influxdata.com/influxdb/cloud/write-data/delete-data/
        """
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

    def delete_bucket(self, missing_ok: bool = True):
        """
        https://docs.influxdata.com/influxdb/v2/admin/buckets/delete-bucket/
        """
        try:
            bucket_id = self.get_bucket_id()
        except KeyError:
            if missing_ok:
                return
            else:
                raise
        try:
            self.client.buckets_api().delete_bucket(bucket_id)
        except influxdb_client.rest.ApiException as ex:
            if ex.status == 404 and missing_ok:
                pass
            else:
                raise

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
                # write_precision=WritePrecision.MS,  # noqa: ERA001
                # data_frame_tag_columns=['tag'],  # noqa: ERA001
            )

    def from_lineprotocol(self, source: t.Union[Path, str], precision: str = "ns"):
        """
        Import data from file in lineprotocol format (ILP) by invoking `influx write`.

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
        except Exception:  # noqa: S110
            pass

        logger.info(f"Importing line protocol format to InfluxDB. bucket={self.bucket}, measurement={self.measurement}")
        self.ensure_bucket()

        if is_url:
            source_option = f'--url="{str(source)}"'
        else:
            source_option = f'--file="{str(source)}"'
        command = f"""
        influx write \
            --host="{self.url}" \
            --token="{self.token}" \
            --org="{self.org}" \
            --bucket="{self.bucket}" \
            --precision={precision} \
            --format=lp \
            {source_option}
        """
        # print("command:", command)  # noqa: ERA001
        run_command(command)

    def get_bucket_id(self):
        """
        Resolve bucket name to bucket id.
        """
        bucket: influxdb_client.Bucket = self.client.buckets_api().find_bucket_by_name(bucket_name=self.bucket)
        if bucket is None:
            raise KeyError(f"Bucket not found: {self.bucket}")
        return bucket.id

    def to_lineprotocol(self, engine_path: str, output_path: t.Union[str, Path]):
        """
        Export data into lineprotocol format (ILP) by invoking `influxd inspect export-lp`.

        TODO: Using a hyphen `-` for `--output-path` works well now, so export can also go to stdout.
        TODO: By default, it will *append* to the .lp file.
              Make it configurable to "replace" data.
        TODO: Make it configurable to use compression, or not.
        TODO: Propagate `--start` and `--end` parameters.
        TODO: Capture stderr messages, and forward user admonition.
              »detected deletes in WAL file, some deleted data may be brought back by replaying this export«
              -- https://github.com/influxdata/influxdb/issues/24456

        https://docs.influxdata.com/influxdb/v2.6/migrate-data/migrate-oss/
        """
        logger.info("Exporting data to InfluxDB line protocol format (ILP)")
        bucket_id = self.get_bucket_id()
        command = f"""
        influxd inspect export-lp \
            --engine-path '{engine_path}' \
            --bucket-id '{bucket_id}' \
            --measurement '{self.measurement}' \
            --output-path '{output_path}' \
            --compress
        """
        run_command(command)


def decode_database_table(url: URL):
    """
    Decode database and table names from database URI path and/or query string.

    Variants:

        /<database>/<table>
        ?database=<database>&table=<table>
        ?schema=<database>&table=<table>
    """
    try:
        database, table = url.path.strip("/").split("/")
    except ValueError as ex:
        if "too many values to unpack" not in str(ex) and "not enough values to unpack" not in str(ex):
            raise
        database = url.query.get("database")
        table = url.query.get("table")
        if url.scheme == "crate" and not database:
            database = url.query.get("schema")
    return database, table


class SqlAlchemyAdapter:
    """
    Adapter to talk to SQLAlchemy-compatible databases.
    """

    def __init__(self, url: t.Union[URL, str], progress: bool = False, debug: bool = False):
        self.progress = progress

        if isinstance(url, str):
            url: URL = URL(url)

        self.database, self.table = decode_database_table(url)

        # Special handling for SQLite and CrateDB databases.
        self.dburi = str(url.with_query(None))
        if url.scheme == "crate":
            url = url.with_path("")
            if self.database:
                url = url.with_query({"schema": self.database})
            self.dburi = str(url)
        elif url.scheme == "sqlite":
            self.dburi = self.dburi.replace("sqlite:/", "sqlite:///")
        else:
            url = url.with_path(self.database)
            self.dburi = str(url)

        logger.info(f"SQLAlchemy DB URI: {self.dburi}")

    @classmethod
    def from_url(cls, url: t.Union[URL, str], **kwargs) -> "SqlAlchemyAdapter":
        return cls(url=url, **kwargs)

    def write(self, source: t.Union[pd.DataFrame, InfluxDbAdapter]):
        logger.info("Loading dataframes into RDBMS/SQL database using pandas/Dask")
        if isinstance(source, InfluxDbAdapter):
            for df in source.read_df():
                dataframe_to_sql(df, dburi=self.dburi, tablename=self.table, progress=self.progress)
        elif isinstance(source, pd.DataFrame):
            dataframe_to_sql(source, dburi=self.dburi, tablename=self.table, progress=self.progress)
        else:
            raise NotImplementedError(f"Failed handling source: {source}")

    def refresh_table(self):
        engine = sa.create_engine(self.dburi)
        with engine.connect() as connection:
            return connection.execute(sa.text(f"REFRESH TABLE {self.table};"))

    def read_records(self) -> t.List[t.Dict]:
        engine = sa.create_engine(self.dburi)
        with engine.connect() as connection:
            result = connection.execute(sa.text(f"SELECT * FROM {self.table};"))  # noqa: S608
            records = [dict(item) for item in result.mappings().fetchall()]
            return records

    def create_database(self):
        try:
            return create_database(self.dburi)
        except sqlalchemy.exc.ProgrammingError as ex:
            if "psycopg2.errors.DuplicateDatabase" not in str(ex):
                raise

    def run_sql(self, sql: str):
        engine = sa.create_engine(self.dburi)
        with engine.connect() as connection:
            connection.connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            return connection.execute(sa.text(sql))

    def run_sql_raw(self, sql: str):
        engine = sa.create_engine(self.dburi)
        connection = engine.raw_connection()
        connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result
