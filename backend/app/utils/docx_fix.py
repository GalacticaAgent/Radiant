from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple
from zipfile import ZipFile, ZIP_DEFLATED

import xml.etree.ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


@dataclass
class DocxFixChange:
    kind: str
    target: str
    before: Dict[str, Any]
    after: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "target": self.target,
            "before": self.before,
            "after": self.after,
        }


def _qn(tag: str) -> str:
    if tag.startswith("{"):
        return tag
    return f"{{{W_NS}}}{tag}"


def _get_or_create(parent: ET.Element, tag: str) -> ET.Element:
    el = parent.find(f"w:{tag}", NS)
    if el is None:
        el = ET.SubElement(parent, _qn(tag))
    return el


def _style_id(style_el: ET.Element) -> Optional[str]:
    return style_el.attrib.get(_qn("styleId")) or style_el.attrib.get(f"{{{W_NS}}}styleId")


def _read_style_values(style_el: ET.Element) -> Dict[str, Any]:
    out: Dict[str, Any] = {"font": None, "size_pt": None, "line_spacing_pt": None}
    rpr = style_el.find(".//w:rPr", NS)
    ppr = style_el.find(".//w:pPr", NS)
    if rpr is not None:
        rf = rpr.find(".//w:rFonts", NS)
        if rf is not None:
            out["font"] = (
                rf.attrib.get(_qn("eastAsia"))
                or rf.attrib.get(_qn("ascii"))
                or rf.attrib.get(_qn("hAnsi"))
            )
        sz = rpr.find(".//w:sz", NS)
        if sz is not None:
            v = sz.attrib.get(_qn("val"))
            if v is not None and str(v).strip():
                try:
                    out["size_pt"] = float(v) / 2.0
                except Exception:
                    out["size_pt"] = None
    if ppr is not None:
        spacing = ppr.find(".//w:spacing", NS)
        if spacing is not None:
            line = spacing.attrib.get(_qn("line"))
            if line is not None and str(line).strip():
                try:
                    out["line_spacing_pt"] = float(line) / 20.0
                except Exception:
                    out["line_spacing_pt"] = None
    return out


def _apply_style_target(style_el: ET.Element, target: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    before = _read_style_values(style_el)
    rpr = style_el.find(".//w:rPr", NS)
    if rpr is None:
        rpr = ET.SubElement(style_el, _qn("rPr"))
    ppr = style_el.find(".//w:pPr", NS)
    if ppr is None:
        ppr = ET.SubElement(style_el, _qn("pPr"))

    after = dict(before)

    font = target.get("font")
    if isinstance(font, str) and font.strip():
        rf = rpr.find(".//w:rFonts", NS)
        if rf is None:
            rf = ET.SubElement(rpr, _qn("rFonts"))
        for k in ("eastAsia", "ascii", "hAnsi"):
            rf.attrib[_qn(k)] = font.strip()
        after["font"] = font.strip()

    size_pt = target.get("size_pt")
    if isinstance(size_pt, (int, float)) and float(size_pt) > 0:
        sz = rpr.find(".//w:sz", NS)
        if sz is None:
            sz = ET.SubElement(rpr, _qn("sz"))
        sz.attrib[_qn("val")] = str(int(round(float(size_pt) * 2.0)))
        after["size_pt"] = float(size_pt)

    line_spacing_pt = target.get("line_spacing_pt")
    if isinstance(line_spacing_pt, (int, float)) and float(line_spacing_pt) > 0:
        spacing = ppr.find(".//w:spacing", NS)
        if spacing is None:
            spacing = ET.SubElement(ppr, _qn("spacing"))
        spacing.attrib[_qn("line")] = str(int(round(float(line_spacing_pt) * 20.0)))
        spacing.attrib[_qn("lineRule")] = "auto"
        after["line_spacing_pt"] = float(line_spacing_pt)

    return before, after


def _footer_has_page_field(root: ET.Element) -> bool:
    for fld in root.findall(".//w:fldSimple", NS):
        instr = fld.attrib.get(_qn("instr")) or ""
        if "PAGE" in instr.upper():
            return True
    text = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8", errors="ignore")
    return "PAGE" in text.upper()


def _ensure_footer_page_field(footer_xml: bytes) -> Tuple[bytes, bool]:
    root = ET.fromstring(footer_xml)
    if _footer_has_page_field(root):
        return footer_xml, False

    ps = root.findall(".//w:p", NS)
    p = ps[-1] if ps else ET.SubElement(root, _qn("p"))
    fld = ET.SubElement(p, _qn("fldSimple"))
    fld.attrib[_qn("instr")] = "PAGE"
    r = ET.SubElement(fld, _qn("r"))
    t = ET.SubElement(r, _qn("t"))
    t.text = "1"
    out = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return out, True


def apply_docx_fixes(
    docx_bytes: bytes,
    *,
    style_targets: Dict[str, Dict[str, Any]],
    ensure_page_numbers: bool = True,
) -> Tuple[bytes, Dict[str, Any]]:
    changes: List[DocxFixChange] = []
    skipped: List[str] = []

    in_buf = BytesIO(docx_bytes or b"")
    out_buf = BytesIO()
    with ZipFile(in_buf) as zin:
        with ZipFile(out_buf, mode="w", compression=ZIP_DEFLATED) as zout:
            names = zin.namelist()
            styles_name = "word/styles.xml"
            styles_xml = None
            if styles_name in names:
                styles_xml = zin.read(styles_name)
            else:
                skipped.append("styles.xml not found")

            updated_styles_bytes = None
            if styles_xml is not None and style_targets:
                try:
                    root = ET.fromstring(styles_xml)
                    target_ids = set(style_targets.keys())
                    for style_el in root.findall(".//w:style", NS):
                        sid = _style_id(style_el)
                        if not sid or sid not in target_ids:
                            continue
                        before, after = _apply_style_target(style_el, style_targets.get(sid) or {})
                        if before != after:
                            changes.append(DocxFixChange(kind="style_update", target=sid, before=before, after=after))
                    updated_styles_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                except Exception:
                    skipped.append("styles.xml parse failed")

            updated_footers: Dict[str, bytes] = {}
            if ensure_page_numbers:
                for n in names:
                    low = n.lower()
                    if not (low.startswith("word/footer") and low.endswith(".xml")):
                        continue
                    try:
                        b = zin.read(n)
                        b2, changed = _ensure_footer_page_field(b)
                        if changed:
                            updated_footers[n] = b2
                            changes.append(
                                DocxFixChange(
                                    kind="footer_page_number",
                                    target=n,
                                    before={"has_page_number": False},
                                    after={"has_page_number": True},
                                )
                            )
                    except Exception:
                        skipped.append(f"footer parse failed: {n}")

            for n in names:
                if n == styles_name and updated_styles_bytes is not None:
                    zout.writestr(n, updated_styles_bytes)
                    continue
                if n in updated_footers:
                    zout.writestr(n, updated_footers[n])
                    continue
                zout.writestr(n, zin.read(n))

    result = {
        "changes": [c.to_dict() for c in changes],
        "skipped": skipped,
    }
    return out_buf.getvalue(), result

