import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from notebook.document import Document, FormulaBlock, TextBlock
from notebook.renderer import NotebookRenderer


def build_sample_document() -> Document:
    doc = Document()
    doc.add_block(TextBlock("Intro"))
    doc.add_block(FormulaBlock("y = 3"))
    doc.add_block(FormulaBlock("x = 2 * y"))
    return doc


def test_static_html_can_embed_local_mathjax(tmp_path: Path):
    renderer = NotebookRenderer()
    doc = build_sample_document()

    mathjax_bundle = tmp_path / "mathjax.js"
    mathjax_bundle.write_text("console.log('mathjax offline');", encoding="utf-8")

    html_output = renderer.render(doc, mathjax_path=str(mathjax_bundle))

    assert "mathjax offline" in html_output
    assert "$$" in html_output
    assert "Variables" in html_output

    output_file = tmp_path / "notebook.html"
    doc.save_html(output_file, renderer=renderer, mathjax_path=str(mathjax_bundle))
    saved_html = output_file.read_text(encoding="utf-8")
    assert "mathjax offline" in saved_html


def test_markdown_export_includes_formulas_and_variables(tmp_path: Path):
    doc = build_sample_document()

    markdown = doc.to_markdown()

    assert "$$" in markdown
    assert "## Variables" in markdown
    assert "| x |" in markdown or "| y |" in markdown

    md_path = tmp_path / "notebook.md"
    doc.save_markdown(md_path)
    assert md_path.read_text(encoding="utf-8") == markdown
