from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import re
from typing import Dict


def extract_docx_style_snapshot(file_content: bytes) -> Dict:
    with ZipFile(BytesIO(file_content)) as z:
        names = z.namelist()
        has_header = any(n.lower().startswith("word/header") and n.lower().endswith(".xml") for n in names)
        has_footer = any(n.lower().startswith("word/footer") and n.lower().endswith(".xml") for n in names)

        has_page_number = False
        for n in names:
            low = n.lower()
            if not (low.startswith("word/footer") and low.endswith(".xml")):
                continue
            footer_xml = z.read(n).decode("utf-8", errors="ignore")
            if re.search(r"\bPAGE\b", footer_xml):
                has_page_number = True
                break

        styles: Dict[str, Dict] = {}
        try:
            styles_xml = z.read("word/styles.xml")
            root = ET.fromstring(styles_xml)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            for style in root.findall(".//w:style", ns):
                style_id = style.attrib.get(f"{{{ns['w']}}}styleId")
                if not style_id:
                    continue
                if style_id not in {"Normal", "Heading1", "Heading2", "Heading3", "Heading4"}:
                    continue

                rpr = style.find(".//w:rPr", ns)
                ppr = style.find(".//w:pPr", ns)

                font = None
                size_pt = None
                line_spacing_pt = None

                if rpr is not None:
                    rf = rpr.find(".//w:rFonts", ns)
                    if rf is not None:
                        font = (
                            rf.attrib.get(f"{{{ns['w']}}}eastAsia")
                            or rf.attrib.get(f"{{{ns['w']}}}ascii")
                            or rf.attrib.get(f"{{{ns['w']}}}hAnsi")
                        )
                    sz = rpr.find(".//w:sz", ns)
                    if sz is not None:
                        v = sz.attrib.get(f"{{{ns['w']}}}val")
                        if v is not None and str(v).strip():
                            size_pt = float(v) / 2.0

                if ppr is not None:
                    spacing = ppr.find(".//w:spacing", ns)
                    if spacing is not None:
                        line = spacing.attrib.get(f"{{{ns['w']}}}line")
                        if line is not None and str(line).strip():
                            line_spacing_pt = float(line) / 20.0

                styles[style_id] = {"font": font, "size_pt": size_pt, "line_spacing_pt": line_spacing_pt}
        except Exception:
            styles = {}

    return {
        "has_header": has_header,
        "has_footer": has_footer,
        "has_page_number": has_page_number,
        "styles": styles,
    }
