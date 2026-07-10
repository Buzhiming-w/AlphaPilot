from __future__ import annotations

from dataclasses import dataclass

from .settings import get_report_translation_model, get_report_translation_provider


@dataclass
class ReportTranslator:
    """LLM-backed translator for persisted final reports."""

    provider: str | None = None
    model: str | None = None

    def __post_init__(self) -> None:
        self.provider = self.provider or get_report_translation_provider()
        self.model = self.model or get_report_translation_model()

    def translate_final_report(self, report: str) -> str:
        from tradingagents.llm_clients.factory import create_llm_client

        prompt = (
            "You are AlphaPilot's report localization worker. Translate the following full "
            "English investment research report into natural Chinese. Preserve the same "
            "section structure, investment conclusion, key numbers, tables, ticker symbols, "
            "source names, and important English financial terms where useful. Do not add "
            "new analysis, do not remove risk caveats, and do not claim this is financial advice.\n\n"
            "English report:\n"
            f"{report}"
        )
        llm = create_llm_client(
            provider=str(self.provider),
            model=str(self.model),
            temperature=0,
        ).get_llm()
        response = llm.invoke(prompt)
        content = getattr(response, "content", response)
        if isinstance(content, list):
            content = "\n".join(str(part) for part in content if str(part).strip())
        translated = str(content).strip()
        if not translated:
            raise ValueError("Empty translated report")
        return translated
