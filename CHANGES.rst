#########
Changelog
#########


in progress
===========

2024-09-17 v0.5.0
=================
- Unlock loading ILP files into SQLAlchemy databases
- Unlock loading ILP files from HTTP resources

2024-06-23 v0.4.0
=================
- Dask interface: Accept and forward the new ``if-exists`` URL query
  parameter to Dask's ``to_sql()`` method.

2024-06-13 v0.3.1
=================
- SQLAlchemy Dialect: Dependencies: Use `sqlalchemy-cratedb>=0.37.0`
  This includes the fix to the `get_table_names()` reflection method.

2024-06-11 v0.3.0
=================
- Dependencies: Migrate from ``crate[sqlalchemy]`` to ``sqlalchemy-cratedb``

2024-05-30 v0.2.1
=================
- Fix CrateDB Cloud connectivity by propagating ``ssl=true`` query argument

2024-04-10 v0.2.0
=================
- Export data from InfluxDB API and data directory into line protocol format

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
