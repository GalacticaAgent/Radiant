from app.services.llm_service import LLMService


def test_ensure_format_rule_payload_normalizes_fields():
    raw = {
        "rule_name": "示例规则",
        "summary": "用于测试",
        "rules": [
            {"key": "a", "severity": "major", "requirement": "标题不超过 36 字", "how_to_check": "统计标题字数", "suggestion": "缩短标题"},
            {"id": "b", "description": "参考文献按 [n] 编号", "check_method": "检查是否存在 [1] 等标注", "suggestion": "统一编号"},
            "bad",
            {"id": "", "severity": "", "description": "  ", "suggestion": "x"},
        ],
    }
    payload = LLMService._ensure_format_rule_payload(raw)
    assert payload["name"] == "示例规则"
    assert payload["mode"] in ("augment", "replace")
    assert isinstance(payload["llm_rules"], list)
    assert len(payload["llm_rules"]) == 2
    assert payload["llm_rules"][0]["id"] == "a"
    assert payload["llm_rules"][0]["description"] == "标题不超过 36 字"
    assert payload["llm_rules"][1]["severity"] in ("major", "minor", "critical")
