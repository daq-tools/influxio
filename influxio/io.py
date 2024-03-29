import logging
import os
import typing as t
from collections import OrderedDict
from pathlib import Path

import fsspec
import pandas as pd

logger = logging.getLogger(__name__)


BytesString = t.Union[bytes, str]
BytesStringList = t.List[BytesString]


def open(path: t.Union[Path, str]):  # noqa: A001
    """
    Access a plethora of resources using `fsspec`.
    """
    path = str(path)
    kwargs: t.Dict[str, t.Any] = {}

    # TODO: Also support authenticated S3.
    if path.startswith("s3"):
        kwargs["anon"] = True

    # TODO: Why isn't compression selected transparently?
    if path.endswith(".gz"):
        kwargs["compression"] = "gzip"
    fs = fsspec.open(path, mode="rb", **kwargs).open()
    return fs


def read_lineprotocol(data: t.IO[t.Any]):
    """
    Read stream of InfluxDB line protocol and decode raw data.

    https://docs.influxdata.com/influxdb/latest/reference/syntax/line-protocol/
    """
    from line_protocol_parser import LineFormatError, parse_line

    for line in data.readlines():
        try:
            yield parse_line(line)
        except LineFormatError as ex:
            logger.info(f"WARNING: Line protocol item {line} invalid. Reason: {ex}")


def records_from_lineprotocol(data: t.IO[t.Any]):
    """
    Read stream of InfluxDB line protocol and generate `OrderedDict` records.
    """
    for lp in read_lineprotocol(data=data):
        record = OrderedDict()
        record["time"] = lp["time"]
        for tag, value in lp["tags"].items():
            record[tag] = value
        for field, value in lp["fields"].items():
            record[field] = value
        yield record


def dataframe_from_lineprotocol(data: t.IO[t.Any]):
    """
    Read stream of InfluxDB line protocol into pandas DataFrame.
    """
    records = records_from_lineprotocol(data)
    return pd.DataFrame(records)


def dataframe_to_sql(
    df: pd.DataFrame,
    dburi: str,
    tablename: str,
    index=False,
    chunksize=None,
    if_exists="replace",
    npartitions: int = None,
    progress: bool = False,
):
    """
    Load pandas dataframe into database using Dask.

    https://stackoverflow.com/questions/62404502/using-dasks-new-to-sql-for-improved-efficiency-memory-speed-or-alternative-to
    """
    import dask.dataframe as dd

    # Set a few defaults.
    chunksize = chunksize or 5_000
    npartitions = npartitions or int(os.cpu_count() / 2)

    if progress:
        from dask.diagnostics import ProgressBar

        pbar = ProgressBar()
        pbar.register()

    if dburi.startswith("crate"):
        # TODO: Submit patch to upstream `crate-python`. This is another proof that something is wrong.
        from cratedb_toolkit.sqlalchemy import patch_inspector

        patch_inspector()

        # Use performance INSERT method.
        from crate.client.sqlalchemy.support import insert_bulk

        method = insert_bulk
    else:
        method = "multi"

    # Load data into database.
    ddf = dd.from_pandas(df, npartitions=npartitions)
    return ddf.to_sql(
        tablename,
        uri=dburi,
        index=index,
        chunksize=chunksize,
        if_exists=if_exists,
        method=method,
        parallel=True,
    )
