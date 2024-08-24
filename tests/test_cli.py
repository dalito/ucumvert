import logging
import os
from unittest import mock

import pytest

from ucumvert.cli import main_cli, run_cli_app


def test_run_cli_app_no_args_entrypoint(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["ucumvert"])
    run_cli_app()
    captured = capsys.readouterr()
    assert "usage: ucumvert" in captured.out


def test_run_cli_app_no_args(capsys):
    run_cli_app([])
    captured = capsys.readouterr()
    assert "usage: ucumvert" in captured.out


def test_main_unknown_arg(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main_cli(["--unknown-arg"])
    assert exc_info.value.code == 2  # noqa: PLR2004
    captured = capsys.readouterr()
    assert "ucumvert: error: unrecognized arguments: --unknown-arg" in captured.err


def test_main_version(capsys):
    main_cli(["--version"])
    captured = capsys.readouterr()
    assert captured.out.startswith("ucumvert")


def test_run_mapping_report_generation(tmp_path):
    dst = tmp_path / "mapping.txt"
    main_cli(["--mapping_report", str(dst)])
    expected = dst
    assert expected.exists()


def test_run_grammar_update(tmp_path):
    dst = tmp_path / "ucum_grammar.lark"
    main_cli(["--grammar_update", str(dst)])
    expected = dst
    assert expected.exists()


@pytest.mark.parametrize(("pydot_installed"), [(True), (False)])
def test_run_interactive(monkeypatch, capsys, pydot_installed):
    if not pydot_installed:
        monkeypatch.setattr("ucumvert.HAS_PYDOT", False)
    inputs = ["kg", "missing", "q"]
    input_generator = (i for i in inputs)
    monkeypatch.setattr("builtins.input", lambda _: next(input_generator))
    main_cli(["--interactive"])
    captured = capsys.readouterr()
    assert "Pint <Quantity(1, 'kilogram')>" in captured.out


@mock.patch.dict(os.environ, {"LOGLEVEL": "ERROR"})
def test_valid_config(caplog, tmp_path):
    # Don't remove "temp_config". The fixture avoid global config change.
    dst = tmp_path / "grammar_log.txt"
    main_cli(["-g", str(dst)])
    with caplog.at_level(logging.ERROR):
        main_cli(["-g", str(dst)])
    assert not caplog.text
