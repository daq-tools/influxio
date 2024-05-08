(index)=
# influxio

[![CI][badge-tests]][project-tests]
[![Coverage Status][badge-coverage]][project-codecov]
[![Documentation][badge-documentation]][project-documentation]
[![License][badge-license]][project-license]
[![Downloads per month][badge-downloads-per-month]][project-downloads]

[![Supported Python versions][badge-python-versions]][project-pypi]
[![Status][badge-status]][project-pypi]
[![Package version][badge-package-version]][project-pypi]

» [Documentation]
| [Changelog]
| [PyPI]
| [Issues]
| [Source code]
| [License]


## About

Import and export data into/from InfluxDB, for humans and machines.


## Features

- **Capable:** Connect to the InfluxDB HTTP API, or read from an InfluxDB
  TSM data directory directly.

- **Concise:** All features are available through a single powerful primitive,
  `influxio copy`.

- **Polyglot:** Support I/O operations between InfluxDB, any SQL database
  supported by SQLAlchemy, file formats supported by pandas/Dask, and
  the native InfluxDB line protocol (ILP), on both import and export
  directions.

- **Versatile:** Use it as a command-line program, pipeline element,
  or as a library within your own applications.


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


## Documentation

Please visit the [README](#readme) document to learn what you can do with
the `influxio` package. Effectively, it is all about the `influxio copy`
primitive, which accepts a range of variants on its `SOURCE` and `TARGET`
arguments, in URL formats.


## Development

Contributions are very much welcome. Please visit the [](#sandbox)
documentation to learn about how to spin up a sandbox environment on your
workstation, or create a [ticket][Issues] to report a bug or share an idea
about a possible feature.



```{toctree}
:maxdepth: 3
:caption: Documentation
:hidden:

README <readme>
```

```{toctree}
:maxdepth: 1
:caption: Workbench
:hidden:

changes
backlog
development
```



[Changelog]: https://github.com/daq-tools/influxio/blob/main/CHANGES.rst
[development documentation]: https://influxio.readthedocs.io/development.html
[Documentation]: https://influxio.readthedocs.io/
[Issues]: https://github.com/daq-tools/influxio/issues
[License]: https://github.com/daq-tools/influxio/blob/main/LICENSE
[PyPI]: https://pypi.org/project/influxio/
[Source code]: https://github.com/daq-tools/influxio
[influxio]: https://influxio.readthedocs.io/

[badge-coverage]: https://codecov.io/gh/daq-tools/influxio/branch/main/graph/badge.svg
[badge-documentation]: https://img.shields.io/readthedocs/influxio
[badge-downloads-per-month]: https://pepy.tech/badge/influxio/month
[badge-license]: https://img.shields.io/github/license/daq-tools/influxio.svg
[badge-package-version]: https://img.shields.io/pypi/v/influxio.svg
[badge-python-versions]: https://img.shields.io/pypi/pyversions/influxio.svg
[badge-status]: https://img.shields.io/pypi/status/influxio.svg
[badge-tests]: https://github.com/daq-tools/influxio/actions/workflows/tests.yml/badge.svg
[project-codecov]: https://codecov.io/gh/daq-tools/influxio
[project-documentation]: https://influxio.readthedocs.io/
[project-downloads]: https://pepy.tech/project/influxio/
[project-license]: https://github.com/daq-tools/influxio/blob/main/LICENSE
[project-pypi]: https://pypi.org/project/influxio
[project-tests]: https://github.com/daq-tools/influxio/actions/workflows/tests.yml
