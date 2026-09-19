import pytest

from mcp_traceguard.cli import _exception_messages, build_parser


def test_cli_reports_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out == "mcp-traceguard 1.0.0\n"


def test_nested_exception_groups_are_flattened_for_cli_errors() -> None:
    error = ExceptionGroup(
        "outer",
        [
            ExceptionGroup("inner", [OSError("connection refused")]),
            ValueError("invalid target"),
            OSError("connection refused"),
        ],
    )
    assert _exception_messages(error) == ["connection refused", "invalid target"]
