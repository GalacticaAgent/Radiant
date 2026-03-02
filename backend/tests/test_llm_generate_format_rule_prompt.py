from app.services.llm_service import LLMService


def test_generate_format_rule_does_not_crash_on_prompt_fstring(monkeypatch):
    svc = LLMService()

    def _fake_chat_with_context(*args, **kwargs):
        return '{"name":"X","summary":"","mode":"augment","executable_rules":[],"llm_rules":[]}'

    monkeypatch.setattr(svc, "chat_with_context", _fake_chat_with_context)
    out = svc.generate_format_rule(source_filename="a.docx", extracted_text="hello", docx_style_snapshot={}, language="zh")
    assert isinstance(out, dict)
