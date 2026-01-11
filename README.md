# influxio

[![Tests](https://github.com/pyveci/influxio/actions/workflows/main.yml/badge.svg)](https://github.com/pyveci/influxio/actions/workflows/main.yml)
[![Test coverage](https://img.shields.io/codecov/c/gh/pyveci/influxio.svg)](https://codecov.io/gh/pyveci/influxio/)
[![License](https://img.shields.io/github/license/pyveci/influxio.svg)](https://github.com/pyveci/influxio/blob/main/LICENSE)
[![Downloads](https://pepy.tech/badge/influxio/month)](https://pypi.org/project/influxio/)

[![Python versions](https://img.shields.io/pypi/pyversions/influxio.svg)](https://pypi.org/project/influxio/)
[![Status](https://img.shields.io/pypi/status/influxio.svg)](https://pypi.org/project/influxio/)
[![PyPI version](https://img.shields.io/pypi/v/influxio.svg)](https://pypi.org/project/influxio/)

» [Documentation][project-documentation]
| [Changelog][project-changelog]
| [PyPI][project-pypi]
| [Issues][project-issues]
| [Source code][project-source]
| [License][project-license]

## About

You can use `influxio` to import and export data into/from InfluxDB.
It can be used both as a standalone program, and as a library.

`influxio` is, amongst others, based on the excellent [dask], [fsspec],
[influxdb-client], [influx-line], [line-protocol-parser], [pandas],
[Polars], and [SQLAlchemy] packages.

## Synopsis

```shell
# Export from API to database.
influxio copy \
    "http://example:token@localhost:8086/testdrive/demo" \
    "sqlite://export.sqlite?table=demo"

# Export from data directory to line protocol format.
influxio copy \
    "file:///path/to/influxdb/engine?bucket-id=372d1908eab801a6&measurement=demo" \
    "file://export.lp"
```

## Quickstart

If you are in a hurry, and want to run `influxio` without any installation,
just use the OCI image on Podman or Docker.

```shell
docker run --rm --network=host ghcr.io/daq-tools/influxio \
    influxio copy \
    "http://example:token@localhost:8086/testdrive/demo" \
    "crate://crate@localhost:4200/testdrive/demo"
```

## Setup

Install `influxio` from PyPI.

```shell
pip install influxio
```

## Usage

This section outlines some example invocations of `influxio`, both on the
command line, and per library use. Other than the resources available from
the web, testing data can be acquired from the repository's [testdata] folder.

### Prerequisites

For properly running some of the example invocations outlined below, you will
need an InfluxDB and a CrateDB server. The easiest way to spin up those
instances is to use Podman or Docker.

Please visit the `docs/development.rst` documentation to learn about how to
spin up corresponding sandbox instances on your workstation.

### Command line use

#### Help

```shell
influxio --help
influxio info
influxio copy --help
```

#### Import

Import data from different sources into InfluxDB Server.

```shell
# From test data to API.
# Choose one of dummy, mixed, dateindex, wide.
influxio copy \
    "testdata://dateindex/" \
    "http://example:token@localhost:8086/testdrive/demo"

# With selected amount of rows.
influxio copy \
    "testdata://dateindex/?rows=42" \
    "http://example:token@localhost:8086/testdrive/demo"

# With selected amount of rows and columns (only supported by certain test data sources).
influxio copy \
    "testdata://wide/?rows=42&columns=42" \
    "http://example:token@localhost:8086/testdrive/demo"

# From line protocol file to InfluxDB API.
influxio copy \
    "file://tests/testdata/basic.lp" \
    "http://example:token@localhost:8086/testdrive/demo"

# From line protocol file to InfluxDB API.
influxio copy \
    "https://github.com/influxdata/influxdb2-sample-data/raw/master/air-sensor-data/air-sensor-data.lp" \
    "http://example:token@localhost:8086/testdrive/demo"
```

#### Export from API

Export data from InfluxDB Server into different sinks.

```shell
# From API to database file.
influxio copy \
    "http://example:token@localhost:8086/testdrive/demo" \
    "sqlite:///export.sqlite?table=demo"

# From API to database server.
influxio copy \
    "http://example:token@localhost:8086/testdrive/demo" \
    "crate://crate@localhost:4200/testdrive/demo"

# From API to line protocol file.
influxio copy \
    "http://example:token@localhost:8086/testdrive/demo" \
    "file://export.lp"

# From API to line protocol on stdout.
influxio copy \
    "http://example:token@localhost:8086/testdrive/demo" \
    "file://-?format=lp"
```

#### Load from File

Load data from InfluxDB files into any SQL database supported by SQLAlchemy.

```shell
# From local line protocol file to SQLite.
influxio copy \
    "file://export.lp" \
    "sqlite:///export.sqlite?table=export"

# From local line protocol file to CrateDB.
influxio copy \
    "file://export.lp" \
    "crate://crate@localhost:4200/testdrive/demo"

# From remote line protocol file to SQLite.
influxio copy \
    "https://github.com/influxdata/influxdb2-sample-data/raw/master/air-sensor-data/air-sensor-data.lp" \
    "sqlite:///export.sqlite?table=air-sensor-data"

# From remote line protocol file to CrateDB.
influxio copy \
    "https://github.com/influxdata/influxdb2-sample-data/raw/master/air-sensor-data/air-sensor-data.lp" \
    "crate://crate@localhost:4200/testdrive/demo"
```

#### Export from Cloud to Cloud

```shell
# From InfluxDB Cloud to CrateDB Cloud.
influxio copy \
    "https://8e9ec869a91a3517:T268DVLDHD8AJsjzOEluu...Pic4A==@eu-central-1-1.aws.cloud2.influxdata.com/testdrive/demo" \
    "crate://admin:dZ,Y18*Z...7)6LqB@green-shaak-ti.eks1.eu-west-1.aws.cratedb.net:4200/testdrive/demo?ssl=true"

crash \
    --hosts 'https://admin:dZ,Y18*Z...7)6LqB@green-shaak-ti.eks1.eu-west-1.aws.cratedb.net:4200' \
    --command 'SELECT * FROM testdrive.demo;'
```

#### Export from data directory

```shell
# From InfluxDB data directory to line protocol file.
influxio copy \
    "file:///path/to/influxdb/engine?bucket-id=372d1908eab801a6&measurement=demo" \
    "file://export.lp"

# From InfluxDB data directory to line protocol file, compressed with gzip.
influxio copy \
    "file:///path/to/influxdb/engine?bucket-id=372d1908eab801a6&measurement=demo" \
    "file://export.lp.gz"

# From InfluxDB data directory to line protocol on stdout.
influxio copy \
    "file:///path/to/influxdb/engine?bucket-id=372d1908eab801a6&measurement=demo" \
    "file://-?format=lp"
```

#### OCI

OCI images are available on the GitHub Container Registry (GHCR). In order to
run them on Podman or Docker, invoke:

```shell
docker run --rm --network=host ghcr.io/daq-tools/influxio \
    influxio copy \
    "http://example:token@localhost:8086/testdrive/demo" \
    "stdout://export.lp"
```

If you want to work with files on your filesystem, you will need to either
mount the working directory into the container using the `--volume` option,
or use the `--interactive` option to consume STDIN, like:

```shell
docker run --rm --volume=$(pwd):/data ghcr.io/daq-tools/influxio \
    influxio copy "file:///data/export.lp" "sqlite:///data/export.sqlite?table=export"

cat export.lp | \
docker run --rm --interactive --network=host ghcr.io/daq-tools/influxio \
    influxio copy "stdin://?format=lp" "crate://crate@localhost:4200/testdrive/export"
```

In order to always run the latest `nightly` development version, and to use a
shortcut for that, this section outlines how to use an alias for `influxio`,
and a variable for storing the input URL. It may be useful to save a few
keystrokes on subsequent invocations.

```shell
docker pull ghcr.io/daq-tools/influxio:nightly
alias influxio="docker run --rm --interactive ghcr.io/daq-tools/influxio:nightly influxio"
SOURCE=https://github.com/daq-tools/influxio/raw/main/tests/testdata/basic.lp
TARGET=crate://crate@localhost:4200/testdrive/basic

influxio copy "${SOURCE}" "${TARGET}"
```

### InfluxDB parameters

#### `timeout`

The network timeout value is specified in seconds, the default value
is 60 seconds. Both details deviate from the standard default setting
of the underlying [InfluxDB client library][influxdb-client], which
uses milliseconds, and a default value of 10_000 milliseconds.

If you need to adjust this setting, add the parameter `timeout` to
the InfluxDB URL like this:

```shell
influxio copy \
    "http://example:token@localhost:8086/testdrive/demo?timeout=300" \
    "crate://crate@localhost:4200/testdrive/demo"
```

### CrateDB parameters

#### `if-exists`

When targeting the SQLAlchemy database interface, the target table will be
created automatically, if it does not exist. The `if-exists` URL query
parameter can be used to configure this behavior. The default value is
`fail`.

- fail: Raise a ValueError.
- replace: Drop the table before inserting new values.
- append: Insert new values to the existing table.

Example usage:

```shell
influxio copy \
    "http://example:token@localhost:8086/testdrive/demo" \
    "crate://crate@localhost:4200/testdrive/demo?if-exists=replace"
```

## Project information

### Contribute

Contributions of all kinds are much very welcome, in order to make the
software more solid.

For installing the project from source, please follow the [development]
documentation.

### Status

Breaking changes should be expected until a 1.0 release, so version pinning
is recommended, especially when you use it as a library.

### Prior art

There are a few other projects which are aiming at similar goals.

- [InfluxDB Fetcher]
- [influxdb-write-to-postgresql] (IW2PG)
- [Outflux]

### Supported by

[![JetBrains logo.](https://resources.jetbrains.com/storage/products/company/brand/logos/jetbrains.svg)](https://jb.gg/OpenSourceSupport)

Special thanks to the people at JetBrains s.r.o. for supporting us with
excellent development tooling.


[dask]: https://www.dask.org/
[development]: https://influxio.readthedocs.io/development.html
[fsspec]: https://pypi.org/project/fsspec/
[influx]: https://docs.influxdata.com/influxdb/latest/reference/cli/influx/
[influx-line]: https://github.com/functionoffunction/influx-line
[influxd]: https://docs.influxdata.com/influxdb/latest/reference/cli/influxd/
[influxdb fetcher]: https://github.com/hgomez/influxdb
[influxdb line protocol]: https://docs.influxdata.com/influxdb/latest/reference/syntax/line-protocol/
[influxdb-client]: https://github.com/influxdata/influxdb-client-python
[influxdb-write-to-postgresql]: https://github.com/eras/influxdb-write-to-postgresql
[line-protocol-parser]: https://github.com/Penlect/line-protocol-parser
[outflux]: https://github.com/timescale/outflux
[pandas]: https://pandas.pydata.org/
[polars]: https://pola.rs/
[project-changelog]: https://github.com/daq-tools/influxio/blob/main/CHANGES.rst
[project-documentation]: https://influxio.readthedocs.io
[project-issues]: https://github.com/daq-tools/influxio/issues
[project-license]: https://github.com/daq-tools/influxio/blob/main/LICENSE
[project-pypi]: https://pypi.org/project/influxio/
[project-source]: https://github.com/daq-tools/influxio
[sqlalchemy]: https://pypi.org/project/SQLAlchemy/
[testdata]: https://github.com/daq-tools/influxio/tree/main/tests/testdata
