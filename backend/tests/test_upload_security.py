import inspect

from app.api import upload as upload_api
from app.services.llm_service import LLMService


def test_magic_ok_pdf():
    assert upload_api._magic_ok(".pdf", b"%PDF-1.7") is True
    assert upload_api._magic_ok(".pdf", b"NOTPDF") is False


def test_magic_ok_docx():
    assert upload_api._magic_ok(".docx", b"PK\x03\x04xxxx") is True
    assert upload_api._magic_ok(".docx", b"%PDF-") is False


def test_sensitive_scan():
    assert upload_api._scan_sensitive(b"-----BEGIN PRIVATE KEY-----") is not None
    assert upload_api._scan_sensitive(b"normal text") is None


def test_llm_format_review_signature_has_custom_rule():
    sig = inspect.signature(LLMService.generate_format_review)
    assert "custom_rule_text" in sig.parameters

