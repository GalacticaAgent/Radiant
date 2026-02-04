def build_persona_prompt(persona: dict) -> str:

    sections = []

    if persona.get("title"):
        sections.append(f"ROLE TITLE:\n{persona['title']}")

    if persona.get("identity"):
        sections.append(f"ROLE IDENTITY:\n{persona['identity']}")

    if persona.get("decision_logic"):
        sections.append(
            "DECISION LOGIC (MANDATORY):\n"
            f"{persona['decision_logic']}"
        )

    if persona.get("hard_bias"):
        bias_lines = "\n".join(f"- {b}" for b in persona["hard_bias"])
        sections.append(
            "HARD BIAS (NON-NEGOTIABLE RULES):\n"
            f"{bias_lines}"
        )

    if persona.get("style"):
        sections.append(f"RESPONSE STYLE:\n{persona['style']}")

    return "\n\n".join(sections)


def build_focus_prompt(focus: list) -> str:

    if not focus:
        return ""

    focus_lines = "\n".join(f"- {f}" for f in focus)

    return (
        "PRIMARY EVALUATION FOCUS "
        "(TAKES PRIORITY OVER ALL OTHER FACTORS):\n"
        f"{focus_lines}"
    )