########
influxio
########


*****
About
*****

You can use ``influxio`` to import and export data into/from InfluxDB.
It can be used both as a standalone program, and as a library.

``influxio`` is, amongst others, based on the excellent `dask`_, `fsspec`_,
`influxdb-client`_, `line-protocol-parser`_, `pandas`_, and `SQLAlchemy`_
packages.

Please note that ``influxio`` is alpha-quality software, and a work in progress.
Contributions of all kinds are very welcome, in order to make it more solid.
Breaking changes should be expected until a 1.0 release, so version pinning
is recommended, especially when you use it as a library.

**Caveat**: Only a few features sketched out in the README have actually been
implemented right now.


********
Synopsis
********

.. code-block:: sh

    # Export from data directory to line protocol format.
    influxio copy \
        "file:///path/to/data/engine?org=example&bucket=testdrive&measurement=demo" \
        "file://export.lp"

    # Export from API to database.
    influxio copy \
        "http://example:token@localhost:8086/testdrive/demo" \
        "sqlite://export.sqlite"


**********
Quickstart
**********

If you are in a hurry, and want to run ``influxio`` without any installation,
just use the OCI image on Podman or Docker.

.. code-block:: sh

    docker run --rm --network=host ghcr.io/daq-tools/influxio \
        influxio copy \
        "http://example:token@localhost:8086/testdrive/demo" \
        "crate://crate@localhost:4200/testdrive"


*****
Setup
*****

Install ``influxio`` from PyPI.

.. code-block:: sh

    pip install influxio


*****
Usage
*****

This section outlines some example invocations of ``influxio``, both on the
command line, and per library use. Other than the resources available from
the web, testing data can be acquired from the repository's `testdata`_ folder.

Prerequisites
=============

For properly running some of the example invocations outlined below, you will
need an InfluxDB and a CrateDB server. The easiest way to spin up those
instances is to use Podman or Docker.

.. code-block:: sh

    docker run --rm -it --publish=8086:8086 \
        --env=DOCKER_INFLUXDB_INIT_MODE=setup \
        --env=DOCKER_INFLUXDB_INIT_USERNAME=admin \
        --env=DOCKER_INFLUXDB_INIT_PASSWORD=secret1234 \
        --env=DOCKER_INFLUXDB_INIT_ORG=example \
        --env=DOCKER_INFLUXDB_INIT_BUCKET=default \
        --env=DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=token \
        --volume="$PWD/var/lib/influxdb2:/var/lib/influxdb2" \
        influxdb:2.6

- https://github.com/docker-library/docs/blob/master/influxdb/README.md

.. code-block:: sh

    docker run --rm -it --publish=4200:4200 --publish=5432:5432 \
        --volume="$PWD/var/lib/cratedb:/data" \
        crate:5.2 -Cdiscovery.type=single-node

- https://github.com/docker-library/docs/blob/master/crate/README.md


Command line use
================

Help
----

.. code-block:: sh

    influxio --help
    influxio info
    influxio copy --help

Import
------

.. code-block:: sh

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

    # From line protocol file to API.
    influxio copy \
        "file://tests/testdata/basic.lp" \
        "http://example:token@localhost:8086/testdrive/demo"

    # From line protocol file to API.
    influxio copy \
        "https://github.com/influxdata/influxdb2-sample-data/raw/master/air-sensor-data/air-sensor-data.lp" \
        "http://example:token@localhost:8086/testdrive/demo"

Export
------

.. code-block:: sh

    # From API to database file.
    influxio copy \
        "http://example:token@localhost:8086/testdrive/demo" \
        "sqlite://export.sqlite"

    # From API to database server.
    influxio copy \
        "http://example:token@localhost:8086/testdrive/demo" \
        "crate://crate@localhost:4200/testdrive"

    # From API to line protocol file.
    influxio copy \
        "http://example:token@localhost:8086/testdrive/demo" \
        "file://export.lp"

    # From data directory to line protocol file.
    influxio copy \
        "file:///path/to/data/engine?org=example&bucket=testdrive&measurement=demo" \
        "file://export.lp"

    # From line protocol file to database.
    influxio copy \
        "file://export.lp" \
        "sqlite://export.sqlite"

OCI
---

OCI images are available on the GitHub Container Registry (GHCR). In order to
run them on Podman or Docker, invoke:

.. code-block:: sh

    docker run --rm --network=host ghcr.io/daq-tools/influxio \
        influxio copy \
        "http://example:token@localhost:8086/testdrive/demo" \
        "stdout://export.lp"

If you want to work with files on your filesystem, you will need to either
mount the working directory into the container using the ``--volume`` option,
or use the ``--interactive`` option to consume STDIN, like:

.. code-block:: sh

    docker run --rm --volume=$(pwd):/data ghcr.io/daq-tools/influxio \
        influxio copy "file:///data/export.lp" "sqlite:///data/export.sqlite"

    cat export.lp | \
    docker run --rm --interactive --network=host ghcr.io/daq-tools/influxio \
        influxio copy "stdin://?format=lp" "crate://crate@localhost:4200/testdrive"

In order to always run the latest ``nightly`` development version, and to use a
shortcut for that, this section outlines how to use an alias for ``influxio``,
and a variable for storing the input URL. It may be useful to save a few
keystrokes on subsequent invocations.

.. code-block:: sh

    docker pull ghcr.io/daq-tools/influxio:nightly
    alias influxio="docker run --rm --interactive ghcr.io/daq-tools/influxio:nightly influxio"
    SOURCE=https://github.com/daq-tools/influxio/raw/main/tests/testdata/basic.lp
    TARGET=crate://crate@localhost:4200/testdrive

    influxio copy "${SOURCE}" "${TARGET}"


*******************
Project information
*******************

Development
===========
For installing the project from source, please follow the `development`_
documentation.

Prior art
=========
There are a few other projects which are aiming at similar goals.

- `InfluxDB Fetcher`_
- `influxdb-write-to-postgresql`_ (IW2PG)
- `Outflux`_


.. _dask: https://www.dask.org/
.. _development: doc/development.rst
.. _fsspec: https://pypi.org/project/fsspec/
.. _influx: https://docs.influxdata.com/influxdb/latest/reference/cli/influx/
.. _influxd: https://docs.influxdata.com/influxdb/latest/reference/cli/influxd/
.. _InfluxDB Fetcher: https://github.com/hgomez/influxdb
.. _InfluxDB line protocol: https://docs.influxdata.com/influxdb/latest/reference/syntax/line-protocol/
.. _influxdb-client: https://github.com/influxdata/influxdb-client-python
.. _influxdb-write-to-postgresql: https://github.com/eras/influxdb-write-to-postgresql
.. _line-protocol-parser: https://github.com/Penlect/line-protocol-parser
.. _list of other projects: doc/prior-art.rst
.. _Outflux: https://github.com/timescale/outflux
.. _pandas: https://pandas.pydata.org/
.. _SQLAlchemy: https://pypi.org/project/SQLAlchemy/
.. _testdata: https://github.com/daq-tools/influxio/tree/main/tests/testdata
