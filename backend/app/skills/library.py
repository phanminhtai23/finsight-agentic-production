"""Built-in skills and the default registry."""

from app.skills.base import PromptSkill, SkillRegistry


class SummarizeSkill(PromptSkill):
    name = "summarize"
    description = "Summarize text into a short TL;DR."
    template = (
        "Summarize the following into at most 3 concise bullet points, keeping key figures:\n\n"
        "{input}\n\nSummary:"
    )


class TranslateSkill(PromptSkill):
    name = "translate"
    description = "Translate text to a target language (e.g. English or Vietnamese)."
    template = (
        "Translate the text below into {target_language}. Return ONLY the translation.\n\n{input}"
    )


class FactCheckSkill(PromptSkill):
    name = "fact_check"
    description = "Check whether a claim is supported by the provided evidence."
    template = (
        "Decide if the claim is supported by the evidence.\n"
        "Reply on one line as: SUPPORTED|UNSUPPORTED|UNCLEAR — <short reason>.\n\n"
        "Claim: {claim}\n\nEvidence:\n{evidence}"
    )


def default_registry() -> SkillRegistry:
    return SkillRegistry([SummarizeSkill(), TranslateSkill(), FactCheckSkill()])
