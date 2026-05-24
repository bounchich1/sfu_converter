import json

from docx import Document

from sfu_converter import cli


def test_create_parser_parses_convert_command(tmp_path):
    parser = cli.create_parser()

    args = parser.parse_args(
        [
            "--format",
            "json",
            "--workdir",
            str(tmp_path),
            "convert",
            "--input",
            "input.txt",
            "--output",
            "output.docx",
            "--strict",
        ]
    )

    assert args.command == "convert"
    assert args.format == "json"
    assert args.input.name == "input.txt"
    assert args.output.name == "output.docx"
    assert args.strict is True


def test_convert_command_writes_docx_and_json_result(tmp_path, capsys):
    input_file = tmp_path / "report.txt"
    input_file.write_text("[H1] Report title\n\nBody text", encoding="utf-8")

    exit_code = cli.main(
        [
            "--format",
            "json",
            "--workdir",
            str(tmp_path),
            "convert",
            "--input",
            "report.txt",
            "--output",
            "out/report.docx",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    output_file = tmp_path / "out" / "report.docx"

    assert exit_code == cli.ExitCodes.SUCCESS
    assert output_file.exists()
    assert payload["ok"] is True
    assert payload["command"] == "convert"
    assert payload["diagnostics"] == []
    assert payload["outputs"]["docx"] == str(output_file)

    doc = Document(str(output_file))
    assert [para.text for para in doc.paragraphs if para.text] == [
        "Report title",
        "Body text",
    ]


def test_convert_accepts_common_options_after_subcommand(tmp_path, capsys):
    input_file = tmp_path / "report.txt"
    input_file.write_text("Body text", encoding="utf-8")

    exit_code = cli.main(
        [
            "convert",
            "--input",
            str(input_file),
            "--output",
            str(tmp_path / "report.docx"),
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == cli.ExitCodes.SUCCESS
    assert payload["ok"] is True
    assert payload["command"] == "convert"


def test_convert_command_missing_input_returns_missing_resource(tmp_path, capsys):
    exit_code = cli.main(
        [
            "--format",
            "json",
            "--workdir",
            str(tmp_path),
            "convert",
            "--input",
            "missing.txt",
            "--output",
            "out.docx",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == cli.ExitCodes.MISSING_RESOURCE
    assert payload["ok"] is False
    assert payload["command"] == "convert"
    assert payload["diagnostics"][0]["code"] == "MISSING_INPUT"


def test_validate_docx_command_reports_valid_document(tmp_path, capsys):
    input_file = tmp_path / "report.txt"
    output_file = tmp_path / "report.docx"
    input_file.write_text("[H1] Report title\n\nBody text", encoding="utf-8")
    assert (
        cli.main(
            [
                "--workdir",
                str(tmp_path),
                "convert",
                "--input",
                input_file.name,
                "--output",
                output_file.name,
            ]
        )
        == cli.ExitCodes.SUCCESS
    )

    exit_code = cli.main(
        [
            "--format",
            "json",
            "--workdir",
            str(tmp_path),
            "validate-docx",
            "--input",
            output_file.name,
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out.splitlines()[-1])

    assert exit_code == cli.ExitCodes.SUCCESS
    assert payload["ok"] is True
    assert payload["command"] == "validate-docx"
    assert payload["diagnostics"] == []


def test_validate_docx_command_missing_input_returns_missing_resource(tmp_path, capsys):
    exit_code = cli.main(
        [
            "--format",
            "json",
            "--workdir",
            str(tmp_path),
            "validate-docx",
            "--input",
            "missing.docx",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == cli.ExitCodes.MISSING_RESOURCE
    assert payload["diagnostics"][0]["code"] == "MISSING_INPUT"


def test_interactive_command_launches_legacy_menu(monkeypatch):
    calls = []

    def fake_legacy_main():
        calls.append("called")

    monkeypatch.setattr("sfu_converter.main.main", fake_legacy_main)

    exit_code = cli.main(["interactive"])

    assert exit_code == cli.ExitCodes.SUCCESS
    assert calls == ["called"]


def test_stub_commands_return_internal_error(capsys):
    for command_args in (
        ["parse", "--input", "input.txt"],
        ["lint", "--input", "input.txt"],
        ["list-profiles"],
        ["explain-syntax"],
        ["export-schema", "--schema", "ast"],
    ):
        assert cli.main(command_args) == cli.ExitCodes.INTERNAL_ERROR

    captured = capsys.readouterr()
    assert captured.err.count("Not yet implemented") == 5
