import pytest

from influxio.model import DataFormat, OutputFile


def test_data_format_from_name_success():
    assert DataFormat.from_name("foo.lp") is DataFormat.LINE_PROTOCOL_UNCOMPRESSED
    assert DataFormat.from_name("foo.csv") is DataFormat.ANNOTATED_CSV


def test_data_format_from_name_failure():
    with pytest.raises(ValueError) as ex:
        DataFormat.from_name("foo.bar")
    assert ex.match("Unable to derive data format from file name: foo.bar")


def test_data_format_from_url_filename_success():
    assert DataFormat.from_url("file://foo.lp") is DataFormat.LINE_PROTOCOL_UNCOMPRESSED
    assert DataFormat.from_url("file://foo.csv") is DataFormat.ANNOTATED_CSV


def test_data_format_from_url_filename_failure():
    with pytest.raises(ValueError) as ex:
        DataFormat.from_url("file://foo.bar")
    assert ex.match("Unable to derive data format from URL filename or query parameter: file://foo.bar")


def test_data_format_from_url_query_parameter_success():
    assert DataFormat.from_url("file://-?format=lp") is DataFormat.LINE_PROTOCOL_UNCOMPRESSED
    assert DataFormat.from_url("file://-?format=csv") is DataFormat.ANNOTATED_CSV


def test_data_format_from_url_query_parameter_failure_no_format():
    with pytest.raises(ValueError) as ex:
        DataFormat.from_url("file://-")
    assert ex.match("Unable to derive data format from URL filename or query parameter: file://-")


def test_data_format_from_url_query_parameter_failure_invalid_format():
    with pytest.raises(NotImplementedError) as ex:
        DataFormat.from_url("file://-?format=bar")
    assert ex.match("Invalid data format: bar")


def test_output_file_success_filename(tmp_path):
    file_path = str(tmp_path.with_suffix(".lp").absolute())
    of = OutputFile.from_url(f"file://{file_path}")
    assert of.path == file_path
    assert of.format is DataFormat.LINE_PROTOCOL_UNCOMPRESSED
    assert of.stream.name == file_path


def test_output_file_success_query_parameter():
    of = OutputFile.from_url("file://-?format=lp")
    assert of.path == "-"
    assert of.format is DataFormat.LINE_PROTOCOL_UNCOMPRESSED
    assert of.stream.fileno() == 6


def test_output_file_failure_scheme(tmp_path):
    with pytest.raises(NotImplementedError) as ex:
        DataFormat.from_url("file://-?format=bar")
    assert ex.match("Invalid data format: bar")
