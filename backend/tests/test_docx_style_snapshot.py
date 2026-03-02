from io import BytesIO
from zipfile import ZipFile

from app.utils.docx_inspect import extract_docx_style_snapshot


def test_docx_style_snapshot_detects_header_footer_and_styles():
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:pPr>
      <w:spacing w:line="400" w:lineRule="exact"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:eastAsia="宋体" w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
      <w:sz w:val="21"/>
    </w:rPr>
  </w:style>
</w:styles>
"""
    header_xml = "<w:hdr xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"></w:hdr>"
    footer_xml = "<w:ftr xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">PAGE</w:ftr>"

    buf = BytesIO()
    with ZipFile(buf, "w") as z:
        z.writestr("word/styles.xml", styles_xml)
        z.writestr("word/header1.xml", header_xml)
        z.writestr("word/footer1.xml", footer_xml)
        z.writestr("word/document.xml", "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>")

    snap = extract_docx_style_snapshot(buf.getvalue())
    assert snap["has_header"] is True
    assert snap["has_footer"] is True
    assert snap["has_page_number"] is True
    assert "Normal" in snap["styles"]
    normal = snap["styles"]["Normal"]
    assert normal["font"] == "宋体"
    assert abs(float(normal["size_pt"]) - 10.5) < 0.01
    assert abs(float(normal["line_spacing_pt"]) - 20.0) < 0.01
