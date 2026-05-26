from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path

from sfu_converter.config import PathConfig, SIBFUConfig
from sfu_converter.domain.diagnostics import Diagnostic, DiagnosticCodes, Severity
from sfu_converter.domain.formatting import FormattingProfile, RuleStatus, unsupported_rule_diagnostics
from sfu_converter.infrastructure.docx_validator import diagnostic_to_json
from sfu_converter.parser import get_parser
from sfu_converter.parser.syntax_spec import get_syntax_spec
from sfu_converter.registry import get_profile, iter_profiles


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
    lint_p.add_argument("--syntax-version", type=int, choices=[1, 2], default=1)
    lint_p.add_argument("--strict", action="store_true")

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


_SCHEMAS = {
    "diagnostics": {
        "type": "object",
        "required": ["code", "severity", "message", "ruleId", "source"],
        "properties": {
            "code": {"type": "string"},
            "severity": {"enum": ["info", "warning", "error", "fatal"]},
            "message": {"type": "string"},
            "ruleId": {"type": "string"},
            "source": {"type": "string"},
            "suggestion": {"type": "string"},
        },
    },
    "ast": {
        "type": "object",
        "required": ["type", "blocks", "syntax_version"],
        "properties": {
            "type": {"const": "document"},
            "blocks": {"type": "array"},
            "syntax_version": {"type": "integer"},
            "metadata": {"type": "object"},
            "source_file": {"type": ["string", "null"]},
        },
    },
    "profiles": {
        "type": "object",
        "additionalProperties": {
            "type": "object",
            "required": [
                "name",
                "displayName",
                "sourceDocs",
                "ruleCount",
                "rendererSupportCount",
                "validatorSupportCount",
                "unsupportedRuleIds",
            ],
        },
    },
    "results": {
        "type": "object",
        "required": ["ok", "command", "diagnostics"],
        "properties": {
            "ok": {"type": "boolean"},
            "command": {"type": "string"},
            "inputs": {"type": "object"},
            "outputs": {"type": "object"},
            "profile": {"type": "string"},
            "syntaxVersion": {"type": "integer"},
            "durationMs": {"type": "integer"},
            "diagnostics": {"type": "array"},
        },
    },
}


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    handlers = {
        "convert": cmd_convert,
        "validate-docx": cmd_validate_docx,
        "interactive": cmd_interactive,
        "parse": cmd_parse,
        "lint": cmd_lint,
        "list-profiles": cmd_list_profiles,
        "explain-syntax": cmd_explain_syntax,
        "export-schema": cmd_export_schema,
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
    profile = _resolve_profile_arg(args, "convert")
    if profile is None:
        return ExitCodes.MISSING_RESOURCE

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
        converter.convert_file(
            input_path,
            output_path,
            template=args.template,
            template_mode=args.template_mode,
            insert_after_page=args.insert_after_page,
            insert_at_bookmark=args.insert_at_bookmark,
            syntax_version=args.syntax_version,
            strict=args.strict,
            profile=profile,
        )
    except OSError as exc:
        _emit_write_failure(args, "convert", str(exc))
        return ExitCodes.WRITE_FAILURE

    diagnostics = list(converter.diagnostics)
    if args.validate_output:
        validator = StyleValidator(SIBFUConfig, profile=profile)
        is_valid = validator.validate_file(str(output_path))
        raw_validation_diagnostics = getattr(validator, "diagnostics", None)
        if raw_validation_diagnostics is not None:
            diagnostics.extend(raw_validation_diagnostics)
        elif not is_valid:
            diagnostics.extend(_diagnostics_from_report(validator.get_report()))

    exit_code = _exit_code_from_diagnostics(diagnostics, strict=args.strict)
    diagnostics_json = _diagnostics_to_json(diagnostics)

    duration_ms = int((time.time() - start) * 1000)
    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    "convert",
                    exit_code == ExitCodes.SUCCESS,
                    inputs={"input": str(input_path), "profile": args.profile},
                    outputs={"docx": str(output_path)},
                    profile=profile.name,
                    syntaxVersion=args.syntax_version,
                    durationMs=duration_ms,
                    diagnostics=diagnostics_json,
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        print(f"Converted: {input_path} -> {output_path}")
    return exit_code


def cmd_validate_docx(args) -> int:
    from sfu_converter.validator import StyleValidator

    profile = _resolve_profile_arg(args, "validate-docx")
    if profile is None:
        return ExitCodes.MISSING_RESOURCE

    input_path = _resolve_path(args.workdir, args.input)
    if not input_path.exists():
        _emit_missing_resource(
            args,
            "validate-docx",
            "MISSING_INPUT",
            f"File not found: {input_path}",
        )
        return ExitCodes.MISSING_RESOURCE

    validator = StyleValidator(SIBFUConfig, profile=profile)
    is_valid = validator.validate_file(str(input_path))
    report = validator.get_report()
    raw_diagnostics = getattr(validator, "diagnostics", None)
    if raw_diagnostics is not None:
        diagnostics = _diagnostics_to_json(raw_diagnostics)
    else:
        diagnostics = _validation_diagnostics(report)

    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    "validate-docx",
                    is_valid,
                    inputs={"input": str(input_path), "profile": profile.name},
                    profile=profile.name,
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


def cmd_parse(args) -> int:
    start = time.time()
    input_path = _resolve_path(args.workdir, args.input)
    if not input_path.exists():
        _emit_missing_resource(
            args,
            "parse",
            "MISSING_INPUT",
            f"File not found: {input_path}",
        )
        return ExitCodes.MISSING_RESOURCE

    source = input_path.read_text(encoding="utf-8")
    result = get_parser(args.syntax_version).parse(source, filename=str(input_path))
    exit_code = _exit_code_from_diagnostics(result.diagnostics)
    duration_ms = int((time.time() - start) * 1000)

    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    "parse",
                    exit_code == ExitCodes.SUCCESS,
                    inputs={"input": str(input_path)},
                    outputs={},
                    syntaxVersion=args.syntax_version,
                    ast=_ast_to_json(result.document),
                    durationMs=duration_ms,
                    diagnostics=_diagnostics_to_json(result.diagnostics),
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        print(json.dumps(_ast_to_json(result.document), ensure_ascii=False, indent=2))
    return exit_code


def cmd_lint(args) -> int:
    start = time.time()
    profile = _resolve_profile_arg(args, "lint")
    if profile is None:
        return ExitCodes.MISSING_RESOURCE

    input_path = _resolve_path(args.workdir, args.input)
    if not input_path.exists():
        _emit_missing_resource(
            args,
            "lint",
            "MISSING_INPUT",
            f"File not found: {input_path}",
        )
        return ExitCodes.MISSING_RESOURCE

    source = input_path.read_text(encoding="utf-8")
    result = get_parser(args.syntax_version, strict=args.strict).parse(source, filename=str(input_path))
    diagnostics = list(result.diagnostics)
    diagnostics.extend(unsupported_rule_diagnostics(profile, component="renderer"))
    diagnostics.extend(unsupported_rule_diagnostics(profile, component="validator"))
    exit_code = _exit_code_from_diagnostics(diagnostics, strict=args.strict)
    duration_ms = int((time.time() - start) * 1000)

    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    "lint",
                    exit_code == ExitCodes.SUCCESS,
                    inputs={"input": str(input_path), "profile": profile.name},
                    outputs={},
                    profile=profile.name,
                    syntaxVersion=args.syntax_version,
                    durationMs=duration_ms,
                    diagnostics=_diagnostics_to_json(diagnostics),
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        _print_text_diagnostics(diagnostics)
    return exit_code


def cmd_list_profiles(args) -> int:
    profiles = {profile.name: _profile_to_json(profile) for profile in iter_profiles()}
    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    "list-profiles",
                    True,
                    profiles=profiles,
                    diagnostics=[],
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        for profile in profiles.values():
            print(f"{profile['name']}: {profile['displayName']}")
    return ExitCodes.SUCCESS


def cmd_export_schema(args) -> int:
    schema = _SCHEMAS[args.schema]
    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    "export-schema",
                    True,
                    outputs={"schema": args.schema},
                    schemaName=args.schema,
                    schema=schema,
                    diagnostics=[],
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        print(json.dumps(schema, ensure_ascii=False, indent=2))
    return ExitCodes.SUCCESS


def cmd_interactive(args) -> int:
    from sfu_converter.main import main as legacy_main

    legacy_main()
    return ExitCodes.SUCCESS


def cmd_explain_syntax(args) -> int:
    spec = get_syntax_spec(args.syntax_version)
    if args.format == "json":
        print(
            json.dumps(
                make_json_result(
                    "explain-syntax",
                    True,
                    syntaxVersion=spec["syntaxVersion"],
                    blocks=spec["blocks"],
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        print(f"Syntax version {spec['syntaxVersion']}")
        for block in spec["blocks"]:
            print(f"{block['name']}: {block['description']}")
            print(f"  Marker: {block['marker']}")
            print(f"  Example: {block['example']}")
    return ExitCodes.SUCCESS


def cmd_not_implemented(args) -> int:
    print("Not yet implemented", file=sys.stderr)
    return ExitCodes.INTERNAL_ERROR


def _resolve_profile_arg(args, command: str) -> FormattingProfile | None:
    try:
        return get_profile(args.profile)
    except KeyError:
        _emit_missing_resource(
            args,
            command,
            DiagnosticCodes.MISSING_PROFILE,
            f"Unknown profile: {args.profile}",
        )
        return None


def _exit_code_from_diagnostics(diagnostics: list[Diagnostic], *, strict: bool = False) -> int:
    if _has_errors(diagnostics):
        return ExitCodes.VALIDATION_ERROR
    if strict and any(diagnostic.severity is Severity.WARNING for diagnostic in diagnostics):
        return ExitCodes.WARNINGS_STRICT
    return ExitCodes.SUCCESS


def _has_errors(diagnostics: list[Diagnostic]) -> bool:
    return any(diagnostic.severity in (Severity.ERROR, Severity.FATAL) for diagnostic in diagnostics)


def _diagnostics_to_json(diagnostics: list[Diagnostic]) -> list[dict[str, object]]:
    return [diagnostic_to_json(diagnostic) for diagnostic in diagnostics]


def _diagnostics_from_report(report) -> list[Diagnostic]:
    diagnostics = []
    diagnostics.extend(
        Diagnostic("VALIDATION_ERROR", message, Severity.ERROR)
        for message in report["error_list"]
    )
    diagnostics.extend(
        Diagnostic("VALIDATION_WARNING", message, Severity.WARNING)
        for message in report["warning_list"]
    )
    return diagnostics


def _print_text_diagnostics(diagnostics: list[Diagnostic]) -> None:
    for diagnostic in diagnostics:
        print(
            f"{diagnostic.severity.value.upper()}: {diagnostic.code}: {diagnostic.message}",
            file=sys.stderr,
        )


def _profile_to_json(profile: FormattingProfile) -> dict[str, object]:
    renderer_unsupported = [
        rule.id for rule in profile.rules if rule.renderer_status is RuleStatus.NOT_SUPPORTED
    ]
    validator_unsupported = [
        rule.id for rule in profile.rules if rule.validator_status is RuleStatus.NOT_SUPPORTED
    ]
    return {
        "name": profile.name,
        "displayName": profile.display_name,
        "sourceDocs": list(profile.source_docs),
        "ruleCount": len(profile.rules),
        "rendererSupportCount": len(profile.rules) - len(renderer_unsupported),
        "validatorSupportCount": len(profile.rules) - len(validator_unsupported),
        "unsupportedRuleIds": {
            "renderer": renderer_unsupported,
            "validator": validator_unsupported,
        },
    }


def _ast_to_json(value):
    if is_dataclass(value):
        payload = {"type": _camel_to_snake(value.__class__.__name__.removesuffix("Node"))}
        for field in fields(value):
            payload[field.name] = _ast_to_json(getattr(value, field.name))
        return payload
    if isinstance(value, Enum):
        return value.value if isinstance(value.value, str) else value.name.lower()
    if isinstance(value, Mapping):
        return {key: _ast_to_json(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_ast_to_json(item) for item in value]
    return value


def _camel_to_snake(value: str) -> str:
    chars = []
    for index, char in enumerate(value):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars)


def _resolve_path(workdir: Path, path: Path) -> Path:
    return path if path.is_absolute() else workdir / path


def _template_exists(workdir: Path, template: Path) -> bool:
    if template.is_absolute():
        return template.exists()
    candidates = (
        workdir / PathConfig.TEMPLATES_DIR / template,
        workdir / template,
        template,
    )
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
                    diagnostics=[{"code": "WRITE_FAILURE", "message": message, "severity": "error"}],
                ),
                ensure_ascii=False,
            )
        )
    elif not args.quiet:
        print(f"Error: {message}", file=sys.stderr)


def _validation_diagnostics(report):
    if "diagnostics" in report:
        return report["diagnostics"]

    diagnostics = []
    diagnostics.extend(
        {"code": "VALIDATION_ERROR", "message": message, "severity": "error"} for message in report["error_list"]
    )
    diagnostics.extend(
        {"code": "VALIDATION_WARNING", "message": message, "severity": "warning"} for message in report["warning_list"]
    )
    return diagnostics


if __name__ == "__main__":
    raise SystemExit(main())
