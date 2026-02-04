import json
from utils.llm_client import LLMClient
from utils.prompt_builder import build_persona_prompt, build_focus_prompt


class Reviewer:

    def __init__(self, reviewer_id: str, reviewer_profile: dict):

        self.reviewer_id = reviewer_id
        self.profile = reviewer_profile
        self.paper_content = None

        self.llm = LLMClient()

        persona_prompt = build_persona_prompt(
            self.profile.get("persona", {})
        )
        focus_prompt = build_focus_prompt(
            self.profile.get("focus", [])
        )

        self.system_prompt = f"""
            You are an academic reviewer operating under the following constitution.
    
            {persona_prompt}
    
            {focus_prompt}
    
            GENERAL RULES:
            - Follow decision logic and hard bias strictly
            - Missing justification counts as a weakness
            - Do not speculate beyond the paper content
            - Maintain consistent standards across all tasks
            """.strip()

    def load_paper(self, paper_text: str):
        self.paper_content = paper_text

    def independent_review(self) -> dict:

        if not self.paper_content:
            raise ValueError("Paper not loaded.")

        base_analysis = self._analyze_paper()
        stress_flaws = self._stress_test(base_analysis)

        evidence = self._assemble_evidence(base_analysis, stress_flaws)

        candidate_issues = self._derive_issues_from_stress(stress_flaws)
        verified_issues = self._verify_issues(candidate_issues)

        supported_issues = [
            item["issue"]
            for item in verified_issues
            if item["verdict"] == "SUPPORTED"
        ]

        final_report = self._final_review(evidence, verified_issues)

        return {
            "reviewer_id": self.reviewer_id,
            "identified_issues": supported_issues,
            "issue_verification": verified_issues,
            **final_report
        }

    # =======================
    # Stage 1: Base analysis
    # =======================

    def _analyze_paper(self) -> str:

        user_prompt = f"""
            Below is the full text of a research paper.
    
            --- PAPER START ---
            {self.paper_content}
            --- PAPER END ---
    
            TASK:
            Produce a rigorous, evidence-grounded analysis strictly based on the paper.
    
            ANALYSIS DIMENSIONS:
            1. Focus-specific assessment
            2. Core claims
            3. Critical limitations
            4. Contribution versus flaw trade-off
            """
        return self.llm.ask(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

    # ============================
    # Stage 2: Structured stress test
    # ============================

    def _stress_test(self, base_analysis: str, times: int = 3) -> list:

        flaws = []
        current_context = base_analysis

        for r in range(times):
            user_prompt = f"""
                Below is the full text of a research paper.
    
                --- PAPER START ---
                {self.paper_content}
                --- PAPER END ---
    
                CONTEXT:
                {current_context}
    
                TASK:
                Perform an adversarial stress test.
    
                Identify ONE new critical flaw if it exists.
    
                OUTPUT FORMAT (STRICT JSON):
                {{
                  "flaw": "<concise description>",
                  "category": "missing_proof | invalid_assumption | experimental_gap | logical_inconsistency"
                }}
    
                If no further critical flaws exist, output:
                {{ "done": true }}
    
                STRICTLY PROHIBITED:
                - No markdown
                - No explanations outside JSON
                """

            response = self.llm.ask(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt
            ).strip()

            data = json.loads(response)

            if data.get("done") is True:
                break

            flaw_entry = {
                "round": r + 1,
                "flaw": data["flaw"],
                "category": data["category"]
            }

            flaws.append(flaw_entry)

            current_context += (
                f"\n[Stress Round {r + 1}] "
                f"{data['category']}: {data['flaw']}"
            )

        return flaws

    # ==========================================
    # Stage 3: Stress flaw → candidate issue
    # ==========================================

    def _derive_issues_from_stress(self, stress_flaws: list) -> list:

        user_prompt = f"""
            Below is the full text of a research paper.
    
            --- PAPER START ---
            {self.paper_content}
            --- PAPER END ---
    
            STRESS TEST FINDINGS (JSON):
            {json.dumps(stress_flaws, ensure_ascii=False, indent=2)}
    
            TASK:
            For EACH stress-test flaw, determine whether it constitutes
            a serious unresolved issue in an academic review.
    
            RULES:
            - Do NOT invent new issues
            - Each issue must correspond to exactly one stress flaw
            - If a flaw is minor or redundant, mark it as discarded
    
            OUTPUT FORMAT (STRICT JSON LIST):
            [
              {{
                "stress_flaw": "<original flaw text>",
                "issue": "<formal issue statement or null>",
                "status": "kept | discarded",
                "reason": "<short justification>"
              }}
            ]
    
            STRICTLY PROHIBITED: Do not include any markdown formatting like ```json or any introductory text.
            """

        response = self.llm.ask(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        decisions = json.loads(response)

        return [
            item["issue"]
            for item in decisions
            if item["status"] == "kept" and item["issue"]
        ]

    # ============================
    # Stage 4: Verification
    # ============================

    def _verify_issues(self, issues: list) -> list:

        user_prompt = f"""
            ROLE:
            You are a verification auditor.
    
            PAPER:
            --- PAPER START ---
            {self.paper_content}
            --- PAPER END ---
    
            ISSUES:
            {json.dumps(issues, ensure_ascii=False, indent=2)}
    
            TASK:
            For EACH issue, determine whether it is explicitly supported by the paper text.
    
            STRICT RULES:
            - SUPPORTED only if the paper explicitly contains text justifying it
            - Logical absence or missing proof alone is NOT explicit support
            - You MUST quote exact sentences if supported
    
            OUTPUT FORMAT (STRICT JSON LIST):
            [
              {{
                "issue": "<issue>",
                "verdict": "SUPPORTED | UNSUPPORTED",
                "evidence": "<exact quoted text or null>"
              }}
            ]
    
            STRICTLY PROHIBITED: Do not include any markdown formatting like ```json or any introductory text.
            """

        response = self.llm.ask(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        return json.loads(response)

    # ============================
    # Stage 5: Final review
    # ============================

    def _final_review(self, evidence: str, verified_results: list) -> dict:

        clean_evidence = "\n".join([
            f"PROVEN FLAW: {v['issue']} | SOURCE: {v['evidence']}"
            for v in verified_results if v["verdict"] == "SUPPORTED"
        ])

        user_prompt = f"""
            Below is the full text of a research paper.
    
            --- PAPER START ---
            {self.paper_content}
            --- PAPER END ---
    
            EVIDENCE BASE:
            {evidence}
    
            VERIFIED CRITICAL FLAWS:
            {clean_evidence}
    
            WRITE A FULL ACADEMIC REVIEW WITH:
    
            1. Summary (3–4 sentences)
            2. Key Strengths (3–4 bullet points)
            3. Critical Weaknesses and Rationale (≥250 words)
            4. Final Decision Recommendation
            5. Overall Rating (1–10)
            6. Confidence Score (1–5)
    
            OUTPUT FORMAT (STRICT JSON):
            {{
              "summary": "...",
              "key_strengths": [...],
              "critical_weaknesses": "...",
              "final_decision": "...",
              "overall_rating": 0,
              "confidence_score": 0
            }}
    
            STRICTLY PROHIBITED: Do not include any markdown formatting like ```json or any introductory text.
            """

        response = self.llm.ask(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt
        )

        return json.loads(response)

    # ============================
    # Utilities
    # ============================

    @staticmethod
    def _assemble_evidence(base_analysis: str, stress_flaws: list) -> str:

        formatted_flaws = "\n".join([
            f"[Round {f['round']}] {f['category']}: {f['flaw']}"
            for f in stress_flaws
        ]) if stress_flaws else "None"

        return f"""
        === BASE ANALYSIS ===
        {base_analysis}

        === STRESS TEST FINDINGS ===
        {formatted_flaws}
        """.strip()
