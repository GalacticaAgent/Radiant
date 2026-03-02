from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from uuid import uuid4


def find_soffice() -> Optional[str]:
    env_path = (os.environ.get("SOFFICE_PATH") or "").strip()
    if env_path and os.path.exists(env_path):
        return env_path
    lo_home = (os.environ.get("LIBREOFFICE_HOME") or "").strip()
    if lo_home:
        for rel in (
            r"program\soffice.exe",
            r"program\soffice.com",
            r"program\soffice",
        ):
            p = os.path.join(lo_home, rel)
            if os.path.exists(p):
                return p

    backend_dir = str(Path(__file__).resolve().parents[2])
    local_candidates = [
        os.path.join(backend_dir, r".tools\libreoffice\program\soffice.exe"),
        os.path.join(backend_dir, r".tools\libreoffice\program\soffice.com"),
        os.path.join(backend_dir, r".tools\libreoffice\LibreOffice\program\soffice.exe"),
        os.path.join(backend_dir, r".tools\libreoffice\LibreOffice\program\soffice.com"),
    ]
    for p in local_candidates:
        if os.path.exists(p):
            return p

    for name in ("soffice", "soffice.exe", "soffice.com"):
        p = shutil.which(name)
        if p:
            return p
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        r"C:\Program Files\LibreOffice\program\soffice.com",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.com",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def convert_doc_bytes_to_docx_bytes(doc_bytes: bytes, *, timeout_s: int = 120) -> bytes:
    soffice = find_soffice()
    if not soffice:
        raise ValueError("DOC 解析需要安装 LibreOffice（soffice）或将文件另存为 DOCX/PDF")

    with tempfile.TemporaryDirectory(prefix="radiant_doc_") as tmp:
        tmpdir = Path(tmp)
        base = f"input_{uuid4().hex}"
        src = tmpdir / f"{base}.doc"
        src.write_bytes(doc_bytes or b"")
        cmd = [
            soffice,
            "--headless",
            "--nologo",
            "--nolockcheck",
            "--norestore",
            "--invisible",
            "--convert-to",
            "docx",
            "--outdir",
            str(tmpdir),
            str(src),
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=int(timeout_s))
        if p.returncode != 0:
            msg = (p.stderr or p.stdout or "DOC 转换失败").strip()
            raise ValueError(msg)
        out = tmpdir / f"{base}.docx"
        if out.exists():
            return out.read_bytes()
        docx_files = sorted(tmpdir.glob("*.docx"), key=lambda x: x.stat().st_mtime, reverse=True)
        if docx_files:
            return docx_files[0].read_bytes()
        raise ValueError("DOC 转换失败：未生成 DOCX 文件")
