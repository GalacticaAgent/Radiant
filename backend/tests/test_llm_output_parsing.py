from app.services.llm_service import LLMService


def test_extract_json_any_from_code_fence():
    text = "### 标题\n\n```json\n{\"a\": 1, \"b\": [\"x\"]}\n```\n"
    assert LLMService._extract_json_any(text) == {"a": 1, "b": ["x"]}


def test_extract_json_any_from_raw_json():
    text = "{\"issues\": [], \"overall_grade\": \"合格\", \"priority\": \"中\", \"summary\": \"ok\"}"
    assert LLMService._extract_json_any(text)["overall_grade"] == "合格"


def test_strip_fenced_code_blocks():
    md = "hello\n\n```python\nprint('x')\n```\n\nworld"
    assert LLMService._strip_fenced_code_blocks(md) == "hello\n\nworld"


def test_ensure_review_payload_coerces_types():
    payload = LLMService._ensure_review_payload(
        {
            "strengths": "a\nb",
            "weaknesses": ["c", "  "],
            "suggestions": None,
            "overall_score": "9/10",
            "recommendation": "Accept",
            "confidence": "High",
        }
    )
    assert payload["strengths"] == ["a", "b"]
    assert payload["weaknesses"] == ["c"]
    assert payload["suggestions"] == []
    assert payload["overall_score"] == 9


def test_ensure_format_payload_normalizes_fields():
    payload = LLMService._ensure_format_payload(
        {"issues": [{"severity": "major", "position": "标题", "description": "过长", "suggestion": "缩短"}], "priority": "高"}
    )
    assert isinstance(payload["issues"], list)
    assert payload["priority"] == "高"
