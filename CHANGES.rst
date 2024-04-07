##################
influxio changelog
##################


in progress
===========
- Implement exporting line protocol data from InfluxDB API

2024-03-22 v0.1.2
=================
- Add support for Python 3.12
- Dependencies: Use ``dask[dataframe]``

2023-11-12 v0.1.1
=================
- Fix project metadata

2023-11-12 v0.1.0
=================
- Feature: Copy test data to InfluxDB
- Tests: Speed up test data import by specifying row count
- Tests: Add test for ``influxio info``
- Feature: Add reading line protocol format from file
- Feature: Add reading line protocol format from URL
- Feature: Export from InfluxDB and import into RDBMS,
  using SQLAlchemy/pandas/Dask
