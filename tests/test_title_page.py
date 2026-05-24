from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH

from sfu_converter.config import SIBFUConfig
from sfu_converter.domain.ast_nodes import (
    Document,
    HeadingLevel,
    HeadingNode,
    TitlePageNode,
)
from sfu_converter.domain.formatting import FormattingProfile
from sfu_converter.infrastructure.docx_renderer import DocxRenderer


def _profile():
    return FormattingProfile(
        name="common",
        display_name="Common",
        source_docs=("standard",),
    )


def test_title_page_renders_full_metadata_with_centered_layout(tmp_path):
    metadata = {
        "university": "Сибирский федеральный университет",
        "institute": "Институт космических и информационных технологий",
        "department": "Кафедра вычислительной техники",
        "title": "Отчёт по лабораторной работе №1",
        "subject": "Программирование",
        "student": "Иванов И.И.",
        "group": "КИ22-01Б",
        "supervisor": "Петров П.П.",
        "supervisor_title": "доцент, канд. техн. наук",
        "city": "Красноярск",
        "year": "2026",
    }
    ast = Document(
        blocks=(TitlePageNode(),),
        metadata=metadata,
    )
    output = tmp_path / "title.docx"

    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    renderer.render_to_file(ast, _profile(), str(output))

    doc = DocxDocument(str(output))
    texts = [p.text for p in doc.paragraphs]
    body_xml = doc.element.body.xml

    assert any("МИНИСТЕРСТВО" in t for t in texts)
    assert any("СИБИРСКИЙ ФЕДЕРАЛЬНЫЙ УНИВЕРСИТЕТ" in t for t in texts)
    assert "Институт космических и информационных технологий" in texts
    assert "Кафедра вычислительной техники" in texts
    assert "Отчёт по лабораторной работе №1" in texts
    assert any("Иванов И.И." in t and "Студент" in t for t in texts)
    assert any("Петров П.П." in t and "Руководитель" in t for t in texts)
    assert any("Красноярск" in t and "2026" in t for t in texts)
    assert 'w:type="page"' in body_xml


def test_title_page_renders_with_minimal_metadata(tmp_path):
    metadata = {"title": "Курсовая работа"}
    ast = Document(blocks=(TitlePageNode(),), metadata=metadata)
    output = tmp_path / "title_min.docx"

    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    renderer.render_to_file(ast, _profile(), str(output))

    doc = DocxDocument(str(output))
    texts = [p.text for p in doc.paragraphs]
    assert "Курсовая работа" in texts
    # Default city should always appear
    assert any("Красноярск" in t for t in texts)


def test_title_page_paragraphs_are_centered_and_use_sfu_font(tmp_path):
    ast = Document(
        blocks=(TitlePageNode(),),
        metadata={"title": "Тест", "year": "2026"},
    )
    output = tmp_path / "title_font.docx"

    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    renderer.render_to_file(ast, _profile(), str(output))

    doc = DocxDocument(str(output))
    title_para = next(p for p in doc.paragraphs if p.text == "Тест")
    assert title_para.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert title_para.runs[0].font.name == SIBFUConfig.FONT_NAME
    assert title_para.runs[0].bold is True


def test_title_page_skipped_when_template_mode_is_preserve_prefix(tmp_path):
    ast = Document(
        blocks=(
            TitlePageNode(),
            HeadingNode(level=HeadingLevel.H1, text="Раздел", number="auto"),
        ),
        metadata={"title": "Не должно появиться"},
    )
    output = tmp_path / "title_skipped.docx"

    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    renderer.render_to_file(
        ast,
        _profile(),
        str(output),
        template_mode="preserve-prefix",
    )

    doc = DocxDocument(str(output))
    texts = [p.text for p in doc.paragraphs]
    assert "Не должно появиться" not in texts
    # The body heading still renders
    assert any("Раздел" in t for t in texts)


def test_title_page_first_page_footer_remains_blank(tmp_path):
    ast = Document(
        blocks=(TitlePageNode(),),
        metadata={"title": "Документ"},
    )
    output = tmp_path / "title_footer.docx"

    renderer = DocxRenderer(config_class=SIBFUConfig, base_dir=tmp_path)
    renderer.render_to_file(ast, _profile(), str(output))

    doc = DocxDocument(str(output))
    section = doc.sections[0]
    assert section.different_first_page_header_footer is True
    first_page_footer = section.first_page_footer
    assert first_page_footer.paragraphs[0].text == ""
    assert " PAGE " not in first_page_footer._element.xml
