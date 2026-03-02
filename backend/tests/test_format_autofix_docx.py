from io import BytesIO
from zipfile import ZipFile

from app.main import app
from app.utils.docx_fix import apply_docx_fixes
from app.utils.docx_inspect import extract_docx_style_snapshot


def _make_minimal_docx(*, styles_xml: bytes, footer_xml: bytes) -> bytes:
    buf = BytesIO()
    with ZipFile(buf, mode="w") as z:
        z.writestr("word/styles.xml", styles_xml)
        z.writestr("word/footer1.xml", footer_xml)
    return buf.getvalue()


def test_only_one_auto_fix_route():
    matches = []
    for r in app.routes:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None) or set()
        if path == "/api/format-review/auto-fix" and "POST" in methods:
            matches.append(r)
    assert len(matches) == 1


def test_docx_fix_applies_normal_style_and_footer_page_number():
    styles_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial"/>
      <w:sz w:val="20"/>
    </w:rPr>
    <w:pPr>
      <w:spacing w:line="240"/>
    </w:pPr>
  </w:style>
</w:styles>
"""
    footer_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p><w:r><w:t>footer</w:t></w:r></w:p>
</w:ftr>
"""
    docx_bytes = _make_minimal_docx(styles_xml=styles_xml, footer_xml=footer_xml)
    fixed, result = apply_docx_fixes(
        docx_bytes,
        style_targets={"Normal": {"font": "宋体", "size_pt": 10.5, "line_spacing_pt": 20.0}},
        ensure_page_numbers=True,
    )
    assert isinstance(result, dict)

    snap = extract_docx_style_snapshot(fixed)
    assert snap.get("has_footer") is True
    assert snap.get("has_page_number") is True
    normal = (snap.get("styles") or {}).get("Normal") or {}
    assert "宋体" in str(normal.get("font") or "")
    assert abs(float(normal.get("size_pt") or 0) - 10.5) < 0.25
    assert abs(float(normal.get("line_spacing_pt") or 0) - 20.0) < 0.6

