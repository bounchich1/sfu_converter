import re
from pathlib import Path


def test_standard_documentation_references_exist():
    root = Path(__file__).resolve().parent.parent
    readme = (root / "README.md").read_text(encoding="utf-8")

    section_match = re.search(
        r"## Документация по стандарту и roadmap(?P<section>.*?)(?:\n## |\Z)",
        readme,
        re.S,
    )
    assert section_match is not None

    paths = re.findall(r"`(docs/[^`]+)`", section_match.group("section"))
    assert paths

    missing = [path for path in paths if not (root / path).exists()]
    assert missing == []
