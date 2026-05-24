from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from sfu_converter.config import SIBFUConfig


class ExitCodes:
    SUCCESS = 0
    WARNINGS_STRICT = 1
    VALIDATION_ERROR = 2
    MISSING_RESOURCE = 3
    WRITE_FAILURE = 4
    INTERNAL_ERROR = 5
    INVALID_USAGE = 64


class ConverterArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(ExitCodes.INVALID_USAGE, f"{self.prog}: error: {message}\n")


def create_parser() -> argparse.ArgumentParser:
    parser = ConverterArgumentParser(
        prog="sfu-converter",
        description="TXT to DOCX converter with SFU formatting standards",
    )
    _add_common_options(parser, include_defaults=True)

    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_p = subparsers.add_parser("convert", help="Convert TXT to DOCX")
    _add_common_options(convert_p, include_defaults=False)
    convert_p.add_argument("--input", required=True, type=Path)
    convert_p.add_argument("--output", required=True, type=Path)
    convert_p.add_argument("--profile", default="common")
    convert_p.add_argument("--template", type=Path, default=None)
    convert_p.add_argument(
        "--template-mode",
        choices=["append", "preserve-prefix", "replace-body"],
        default="append",
    )
    convert_p.add_argument("--insert-after-page", type=int, default=None)
    convert_p.add_argument("--insert-at-bookmark", default=None)
    convert_p.add_argument("--syntax-version", type=int, choices=[1, 2], default=1)
    convert_p.add_argument("--strict", action="store_true")
    convert_p.add_argument("--validate-output", action="store_true")
    convert_p.add_argument("--diagnostics", type=Path, default=None)

    validate_p = subparsers.add_parser("validate-docx", help="Validate existing DOCX")
    _add_common_options(validate_p, include_defaults=False)
    validate_p.add_argument("--input", required=True, type=Path)
    validate_p.add_argument("--profile", default="common")

    parse_p = subparsers.add_parser("parse", help="Parse TXT to AST")
    _add_common_options(parse_p, include_defaults=False)
    parse_p.add_argument("--input", required=True, type=Path)
    parse_p.add_argument("--syntax-version", type=int, choices=[1, 2], default=1)

    lint_p = subparsers.add_parser("lint", help="Lint TXT syntax")
    _add_common_options(lint_p, include_defaults=False)
    lint_p.add_argument("--input", required=True, type=Path)
    lint_p.add_argument("--profile", default="common")

    list_profiles_p = subparsers.add_parser("list-profiles", help="List formatting profiles")
    _add_common_options(list_profiles_p, include_defaults=False)

    explain_p = subparsers.add_parser("explain-syntax", help="Show TXT syntax")
    _add_common_options(explain_p, include_defaults=False)
    explain_p.add_argument("--syntax-version", type=int, choices=[1, 2], default=1)

    schema_p = subparsers.add_parser("export-schema", help="Export JSON schemas")
    _add_common_options(schema_p, include_defaults=False)
    schema_p.add_argument(
        "--schema",
        required=True,
        choices=["diagnostics", "ast", "profiles", "results"],
    )

    interactive_p = subparsers.add_parser("interactive", help="Start interactive menu")
    _add_common_options(interactive_p, include_defaults=False)

    return parser


def _add_common_options(parser: argparse.ArgumentParser, include_defaults: bool) -> None:
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text" if include_defaults else argparse.SUPPRESS,
        help="Output format",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False if include_defaults else argparse.SUPPRESS,
        help="Suppress non-essential stderr output",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False if include_defaults else argparse.SUPPRESS,
        help="Disable ANSI color output",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path(".") if include_defaults else argparse.SUPPRESS,
        help="Base directory for relative paths",
    )


def make_json_result(command: str, ok: bool, **kwargs) -> dict:
    return {
        "ok": ok,
        "command": command,
        **kwargs,
        "diagnostics": kwargs.get("diagnostics", []),
    }


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    handlers = {
        "convert": cmd_convert,
        "validate-docx": cmd_validate_docx,
        "interactive": cmd_interactive,
        "parse": cmd_not_implemented,
        "lint": cmd_not_implemented,
        "list-profiles": cmd_not_implemented,
        "explain-syntax": cmd_not_implemented,
        "export-schema": cmd_not_implemented,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return ExitCodes.INVALID_USAGE
    return handler(args)


def cmd_convert(args) -> int:
    from sfu_converter.converter import TextToDocxConverter
    from sfu_converter.validator import StyleValidator

    start = time.time()
    input_path = _resolve_path(args.workdir, args.input)
    output_path = _resolve_path(args.workdir, args.output)

    if not input_path.exists():
        _emit_missing_resource(args, "convert", "MISSING_INPUT", f"File not found: {input_path}")
        return ExitCodes.MISSING_RESOURCE

    if args.template is not None and not _template_exists(args.workdir, args.template):
        _emit_missing_resource(
            args,
            "convert",
            "MISSING_TEMPLATE",
            f"Template not found: {args.template}",
        )
        return ExitCodes.MISSING_RESOURCE

    try:
        converter = TextToDocxConverter(SIBFUConfig, str(args.workdir))
        converter.convert_file(input_path, output_path, template=args.template)
    except OSError as exc:
        _emit_write_failure(args, "convert", str(exc))
        return ExitCodes.WRITE_FAILURE

    diagnostics = []
    exit_code = ExitCodes.SUCCESS
    if args.validate_output:
        validator = StyleValidator(SIBFUConfig)
        is_valid = validator.validate_file(str(output_path))
        diagnostics = _validation_diagnostics(validator.get_report())
        if not is_valid:
            exit_code = ExitCodes.VALIDATION_ERROR

    duration_ms = int((time.time() - start) * 1000)
    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    "convert",
                    exit_code == ExitCodes.SUCCESS,
                    inputs={"input": str(input_path), "profile": args.profile},
                    outputs={"docx": str(output_path)},
                    profile=args.profile,
                    syntaxVersion=args.syntax_version,
                    durationMs=duration_ms,
                    diagnostics=diagnostics,
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        print(f"Converted: {input_path} -> {output_path}")
    return exit_code


def cmd_validate_docx(args) -> int:
    from sfu_converter.validator import StyleValidator

    input_path = _resolve_path(args.workdir, args.input)
    if not input_path.exists():
        _emit_missing_resource(
            args,
            "validate-docx",
            "MISSING_INPUT",
            f"File not found: {input_path}",
        )
        return ExitCodes.MISSING_RESOURCE

    validator = StyleValidator(SIBFUConfig)
    is_valid = validator.validate_file(str(input_path))
    report = validator.get_report()
    diagnostics = _validation_diagnostics(report)

    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    "validate-docx",
                    is_valid,
                    inputs={"input": str(input_path), "profile": args.profile},
                    diagnostics=diagnostics,
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        if is_valid:
            print(f"Validation passed: {input_path}")
        else:
            print(f"Validation failed: {input_path}")
            for err in report["error_list"]:
                print(f"  ERROR: {err}")

    return ExitCodes.SUCCESS if is_valid else ExitCodes.VALIDATION_ERROR


def cmd_interactive(args) -> int:
    from sfu_converter.main import main as legacy_main

    legacy_main()
    return ExitCodes.SUCCESS


def cmd_not_implemented(args) -> int:
    print("Not yet implemented", file=sys.stderr)
    return ExitCodes.INTERNAL_ERROR


def _resolve_path(workdir: Path, path: Path) -> Path:
    return path if path.is_absolute() else workdir / path


def _template_exists(workdir: Path, template: Path) -> bool:
    if template.is_absolute():
        return template.exists()
    candidates = (workdir / "templates" / template, workdir / template, template)
    return any(candidate.exists() for candidate in candidates)


def _emit_missing_resource(args, command: str, code: str, message: str) -> None:
    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    command,
                    False,
                    diagnostics=[{"code": code, "message": message, "severity": "error"}],
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        print(f"Error: {message}", file=sys.stderr)


def _emit_write_failure(args, command: str, message: str) -> None:
    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    command,
                    False,
                    diagnostics=[
                        {"code": "WRITE_FAILURE", "message": message, "severity": "error"}
                    ],
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        print(f"Error: {message}", file=sys.stderr)


def _validation_diagnostics(report):
    diagnostics = []
    diagnostics.extend(
        {"code": "VALIDATION_ERROR", "message": message, "severity": "error"}
        for message in report["error_list"]
    )
    diagnostics.extend(
        {"code": "VALIDATION_WARNING", "message": message, "severity": "warning"}
        for message in report["warning_list"]
    )
    return diagnostics


if __name__ == "__main__":
    raise SystemExit(main())
