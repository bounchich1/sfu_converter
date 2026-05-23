# Task 08: Add CLI Foundation

## Priority: High
## Phase: Phase 1 (Package and baseline CLI)
## Affected files: NEW `src/sfu_converter/cli.py`, MODIFY `src/sfu_converter/main.py`
## References: `docs/technical requirements/03_agent_cli.md`

## Summary

Add a non-interactive CLI using `argparse` with the commands specified in the technical requirements. Start with `convert`, `validate-docx`, `interactive`, and stub the rest.

## Detailed Implementation

### 1. Create `src/sfu_converter/cli.py`

```python
import argparse
import json
import sys
import time
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='sfu-converter',
        description='TXT to DOCX converter with SFU formatting standards',
    )
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                        help='Output format')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress non-essential stderr output')
    parser.add_argument('--no-color', action='store_true',
                        help='Disable ANSI color output')
    parser.add_argument('--workdir', type=Path, default=Path('.'),
                        help='Base directory for relative paths')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # convert command
    convert_p = subparsers.add_parser('convert', help='Convert TXT to DOCX')
    convert_p.add_argument('--input', required=True, type=Path)
    convert_p.add_argument('--output', required=True, type=Path)
    convert_p.add_argument('--profile', default='common')
    convert_p.add_argument('--template', type=Path, default=None)
    convert_p.add_argument('--template-mode',
                           choices=['append', 'preserve-prefix', 'replace-body'],
                           default='append')
    convert_p.add_argument('--insert-after-page', type=int, default=None)
    convert_p.add_argument('--insert-at-bookmark', default=None)
    convert_p.add_argument('--syntax-version', type=int, choices=[1, 2], default=1)
    convert_p.add_argument('--strict', action='store_true')
    convert_p.add_argument('--validate-output', action='store_true')
    convert_p.add_argument('--diagnostics', type=Path, default=None)

    # validate-docx command
    validate_p = subparsers.add_parser('validate-docx', help='Validate existing DOCX')
    validate_p.add_argument('--input', required=True, type=Path)
    validate_p.add_argument('--profile', default='common')

    # parse command (stub)
    parse_p = subparsers.add_parser('parse', help='Parse TXT to AST')
    parse_p.add_argument('--input', required=True, type=Path)
    parse_p.add_argument('--syntax-version', type=int, choices=[1, 2], default=1)

    # lint command (stub)
    lint_p = subparsers.add_parser('lint', help='Lint TXT syntax')
    lint_p.add_argument('--input', required=True, type=Path)
    lint_p.add_argument('--profile', default='common')

    # list-profiles command
    subparsers.add_parser('list-profiles', help='List formatting profiles')

    # explain-syntax command
    explain_p = subparsers.add_parser('explain-syntax', help='Show TXT syntax')
    explain_p.add_argument('--syntax-version', type=int, choices=[1, 2], default=1)

    # export-schema command
    schema_p = subparsers.add_parser('export-schema', help='Export JSON schemas')
    schema_p.add_argument('--schema', required=True,
                          choices=['diagnostics', 'ast', 'profiles', 'results'])

    # interactive command
    subparsers.add_parser('interactive', help='Start interactive menu')

    return parser


# Exit codes per spec
class ExitCodes:
    SUCCESS = 0
    WARNINGS_STRICT = 1
    VALIDATION_ERROR = 2
    MISSING_RESOURCE = 3
    WRITE_FAILURE = 4
    INTERNAL_ERROR = 5
    INVALID_USAGE = 64


def make_json_result(command: str, ok: bool, **kwargs) -> dict:
    """Build a standard JSON result envelope."""
    return {
        'ok': ok,
        'command': command,
        **kwargs,
        'diagnostics': kwargs.get('diagnostics', []),
    }


def cmd_convert(args):
    """Handle the convert command."""
    start = time.time()
    from sfu_converter.config import SIBFUConfig
    from sfu_converter.converter import TextToDocxConverter
    
    input_path = args.workdir / args.input if not args.input.is_absolute() else args.input
    output_path = args.workdir / args.output if not args.output.is_absolute() else args.output
    
    if not input_path.exists():
        if args.format == 'json':
            print(json.dumps(make_json_result('convert', False, diagnostics=[
                {'code': 'MISSING_INPUT', 'message': f'File not found: {input_path}'}
            ])))
        else:
            print(f'Error: File not found: {input_path}', file=sys.stderr)
        return ExitCodes.MISSING_RESOURCE

    converter = TextToDocxConverter(SIBFUConfig, str(args.workdir))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    converter.convert_file(str(input_path), str(output_path), template=args.template)
    
    duration_ms = int((time.time() - start) * 1000)
    if args.format == 'json':
        print(json.dumps(make_json_result(
            'convert', True,
            inputs={'input': str(input_path), 'profile': args.profile},
            outputs={'docx': str(output_path)},
            profile=args.profile,
            syntaxVersion=args.syntax_version,
            durationMs=duration_ms,
        )))
    else:
        print(f'Converted: {input_path} → {output_path}')
    return ExitCodes.SUCCESS


def cmd_validate_docx(args):
    """Handle the validate-docx command."""
    from sfu_converter.config import SIBFUConfig
    from sfu_converter.validator import StyleValidator
    
    input_path = args.workdir / args.input if not args.input.is_absolute() else args.input
    if not input_path.exists():
        if args.format == 'json':
            print(json.dumps(make_json_result('validate-docx', False, diagnostics=[
                {'code': 'MISSING_INPUT', 'message': f'File not found: {input_path}'}
            ])))
        else:
            print(f'Error: File not found: {input_path}', file=sys.stderr)
        return ExitCodes.MISSING_RESOURCE

    validator = StyleValidator(SIBFUConfig)
    is_valid = validator.validate_file(str(input_path))
    report = validator.get_report()
    
    if args.format == 'json':
        print(json.dumps(make_json_result(
            'validate-docx', is_valid,
            inputs={'input': str(input_path), 'profile': args.profile},
            diagnostics=report['error_list'] + report['warning_list'],
        )))
    else:
        if is_valid:
            print(f'Validation passed: {input_path}')
        else:
            print(f'Validation failed: {input_path}')
            for err in report['error_list']:
                print(f'  ERROR: {err}')
    return ExitCodes.SUCCESS if is_valid else ExitCodes.VALIDATION_ERROR


def cmd_interactive(args):
    """Start the legacy interactive menu."""
    from sfu_converter.main import main as legacy_main
    legacy_main()
    return ExitCodes.SUCCESS


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    handlers = {
        'convert': cmd_convert,
        'validate-docx': cmd_validate_docx,
        'interactive': cmd_interactive,
        'parse': lambda a: (print('Not yet implemented', file=sys.stderr), ExitCodes.INTERNAL_ERROR)[1],
        'lint': lambda a: (print('Not yet implemented', file=sys.stderr), ExitCodes.INTERNAL_ERROR)[1],
        'list-profiles': lambda a: (print('Not yet implemented', file=sys.stderr), ExitCodes.INTERNAL_ERROR)[1],
        'explain-syntax': lambda a: (print('Not yet implemented', file=sys.stderr), ExitCodes.INTERNAL_ERROR)[1],
        'export-schema': lambda a: (print('Not yet implemented', file=sys.stderr), ExitCodes.INTERNAL_ERROR)[1],
    }
    
    handler = handlers.get(args.command)
    if handler:
        exit_code = handler(args)
        sys.exit(exit_code or 0)
    else:
        parser.print_help()
        sys.exit(ExitCodes.INVALID_USAGE)
```

### 2. Update `pyproject.toml` entry point

```toml
[project.scripts]
sfu-converter = "sfu_converter.cli:main"
```

### 3. Update `__main__.py`

```python
from sfu_converter.cli import main
if __name__ == '__main__':
    main()
```

## Exit Code Contract

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Completed with warnings (--strict) |
| 2 | Syntax/validation errors |
| 3 | Missing input/image/template/profile |
| 4 | Output write failure |
| 5 | Internal error |
| 64 | Invalid CLI usage |

## Tests to write

Create `tests/test_cli.py`:
- Test `create_parser()` returns valid parser
- Test `convert` command with valid input/output
- Test `convert` command with missing input file (exit code 3)
- Test `validate-docx` with valid file
- Test `validate-docx` with missing file
- Test JSON output format contains required fields (ok, command, diagnostics)
- Test `interactive` command launches menu
- Test stub commands return exit code 5

## Verification

1. `python -m sfu_converter convert --input examples/report_01_basic.txt --output results/test.docx --format json` works
2. `python -m sfu_converter interactive` starts the menu
3. `python -m sfu_converter validate-docx --input results/test.docx --format json` works
4. All stub commands print "Not yet implemented" and exit 5
