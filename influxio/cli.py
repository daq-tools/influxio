import logging

import click

import influxio.core
from influxio.util.cli import boot_click, docstring_format_verbatim
from influxio.util.report import AboutReport

logger = logging.getLogger(__name__)


def help_copy():
    """
    Import and export data into/from InfluxDB

    SOURCE can be a file or a URL.
    TARGET can be a file or a URL.

    Synopsis
    ========

    # Export from data directory to line protocol format.
    influxio copy \
        file:///path/to/data/engine?org=example&bucket=testdrive&measurement=demo \
        file://export.lp

    # Export from API to database.
    influxio copy \
        http://example:token@localhost:8086/testdrive/demo \
        sqlite://export.sqlite

    Examples
    ========

    Export
    ------

    # From API to database file.
    influxio copy \
        http://example:token@localhost:8086/testdrive/demo \
        sqlite:///export.sqlite

    # From API to database server.
    influxio copy \
        http://example:token@localhost:8086/testdrive/demo \
        crate://crate@localhost:4200/testdrive

    # From API to line protocol file.
    influxio copy \
        http://example:token@localhost:8086/testdrive/demo \
        file://export.lp

    # From API to line protocol on stdout.
    influxio copy \
        "http://example:token@localhost:8086/testdrive/demo" \
        "file://-?format=lp"

    # From data directory to line protocol file.
    influxio copy \
        file:///path/to/data/engine?org=example&bucket=testdrive&measurement=demo \
        file://export.lp

    # From line protocol file to database.
    influxio copy \
        file://export.lp \
        sqlite://export.sqlite

    Import
    ------

    # From line protocol file to API.
    influxio copy \
        https://github.com/influxdata/influxdb2-sample-data/raw/master/air-sensor-data/air-sensor-data.lp \
        http://example:token@localhost:8086/testdrive/demo

    # From test data to API.
    influxio copy \
        testdata://dateindex \
        http://example:token@localhost:8086/testdrive/demo

    Documentation
    =============

    More options and examples can be discovered on the influxio README [1].

    [1] https://github.com/daq-tools/influxio/blob/main/README.rst
    """  # noqa: E501


@click.group()
@click.version_option(package_name="influxio")
@click.option("--verbose", is_flag=True, required=False, help="Turn on logging")
@click.option("--debug", is_flag=True, required=False, help="Turn on logging with debug level")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool):
    return boot_click(ctx, verbose, debug)


@cli.command("info", help="Report about platform information")
def info():
    AboutReport.platform()


@cli.command(
    "copy",
    help=docstring_format_verbatim(help_copy.__doc__),
    context_settings={"max_content_width": 120},
)
@click.argument("source", type=str, required=True)
@click.argument("target", type=str, required=True)
@click.pass_context
def copy(ctx: click.Context, source: str, target: str):
    influxio.core.copy(source, target)
    logger.info("Ready.")
