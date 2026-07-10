from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import os
import time
from typing import Any

from .engine_service import AnalysisEngineService
from .queue import RedisAnalysisQueue
from .report_translation import ReportTranslator
from .result_normalizer import make_json_safe
from .settings import (
    get_database_url,
    get_redis_url,
    get_report_translation_max_attempts,
    is_report_translation_enabled,
    is_security_master_auto_sync_enabled,
)
from .security_master.sync import sync_security_master
from .sqlalchemy_store import SqlAlchemyAlphaPilotStore

REPORT_SECTION_LABELS = (
    ("market", "Market report"),
    ("sentiment", "Sentiment"),
    ("news", "News"),
    ("fundamentals", "Fundamentals"),
    ("investment", "Investment debate"),
    ("trader", "Trader plan"),
    ("final", "Final report"),
)


def _translator_provider(translator: Any) -> str | None:
    return getattr(translator, "provider", None)


def _translator_model(translator: Any) -> str | None:
    return getattr(translator, "model", None)


def build_full_report_markdown(normalized: dict[str, Any]) -> str:
    sections = normalized.get("sections") or {}
    parts = []
    for key, label in REPORT_SECTION_LABELS:
        content = sections.get(key)
        if content:
            parts.append(f"## {label}\n\n{content}")
    return "\n\n---\n\n".join(parts)


def ensure_chinese_report_translation(
    *,
    store,
    job,
    translator=None,
    max_attempts: int | None = None,
):
    if not job.result_id:
        return None
    result = store.get_result(job.result_id)
    if not result:
        return None

    normalized = deepcopy(result.normalized)
    cached_final = (
        normalized.get("localized_sections", {})
        .get("zh", {})
        .get("report")
    )
    if cached_final:
        return result

    full_report = build_full_report_markdown(normalized)
    if not full_report:
        translations = normalized.setdefault("report_translations", {})
        translations["zh"] = {
            "status": "skipped",
            "attempts": 0,
            "error": "No English report content available for translation.",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return store.update_result_normalized(result.id, normalized)

    if translator is None:
        if not is_report_translation_enabled():
            return result
        translator = ReportTranslator()

    attempts = max_attempts or get_report_translation_max_attempts()
    store.create_analysis_progress_event(
        job_id=job.id,
        stage_key="translation_zh",
        stage_label="Chinese report",
        status="running",
        summary="Generating cached Chinese report from the completed English report.",
    )

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            translated = translator.translate_final_report(str(full_report))
            zh_sections = normalized.setdefault("localized_sections", {}).setdefault("zh", {})
            zh_sections["report"] = translated
            normalized.setdefault("report_translations", {})["zh"] = {
                "status": "completed",
                "attempts": attempt,
                "provider": _translator_provider(translator),
                "model": _translator_model(translator),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            updated = store.update_result_normalized(result.id, make_json_safe(normalized))
            store.create_analysis_progress_event(
                job_id=job.id,
                stage_key="translation_zh",
                stage_label="Chinese report",
                status="completed",
                summary="Chinese report generated and cached.",
            )
            store.log_api_usage(
                user_id=job.user_id,
                endpoint="analysis.worker.translation.zh",
                provider=_translator_provider(translator),
                model=_translator_model(translator),
            )
            return updated
        except Exception as exc:
            last_error = exc

    normalized.setdefault("report_translations", {})["zh"] = {
        "status": "failed",
        "attempts": attempts,
        "provider": _translator_provider(translator),
        "model": _translator_model(translator),
        "error": str(last_error) if last_error else "Unknown translation failure",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    updated = store.update_result_normalized(result.id, make_json_safe(normalized))
    store.create_analysis_progress_event(
        job_id=job.id,
        stage_key="translation_zh",
        stage_label="Chinese report",
        status="failed",
        summary=str(last_error) if last_error else "Chinese report translation failed.",
    )
    store.log_api_usage(
        user_id=job.user_id,
        endpoint="analysis.worker.translation.zh.failed",
        provider=_translator_provider(translator),
        model=_translator_model(translator),
    )
    return updated


def process_analysis_job(*, store, engine: AnalysisEngineService, job_id: str, translator=None):
    try:
        job = store.mark_job_running(job_id)
    except KeyError:
        return None
    try:
        store.create_analysis_progress_event(
            job_id=job.id,
            stage_key="running",
            stage_label="Workflow started",
            status="running",
            summary=f"Starting {job.ticker} analysis for {job.trade_date}.",
        )
        if job.mode == "demo":
            normalized, raw_state = engine.run_demo()
            endpoint = "analysis.worker.demo"
        else:
            store.create_analysis_progress_event(
                job_id=job.id,
                stage_key="market",
                stage_label="Market analyst",
                status="running",
                summary="Collecting market data and generating the first analyst report.",
            )
            normalized, raw_state = engine.run_live(
                job.ticker,
                job.trade_date,
                job.selected_analysts,
            )
            endpoint = "analysis.worker.live"
        if store.get_job(job.id) is None:
            return None
        completed = store.complete_job(job.id, make_json_safe(normalized), make_json_safe(raw_state))
        store.create_analysis_progress_event(
            job_id=job.id,
            stage_key="final",
            stage_label="Final report",
            status="completed",
            summary="Analysis completed and final report persisted.",
        )
        store.log_api_usage(
            user_id=job.user_id,
            endpoint=endpoint,
            provider=os.getenv("TRADINGAGENTS_LLM_PROVIDER"),
            model=os.getenv("TRADINGAGENTS_DEEP_THINK_LLM") or os.getenv("TRADINGAGENTS_QUICK_THINK_LLM"),
        )
        ensure_chinese_report_translation(store=store, job=completed, translator=translator)
        return completed
    except Exception as exc:
        if store.get_job(job.id) is None:
            return None
        try:
            failed = store.fail_job(job.id, str(exc))
            store.create_analysis_progress_event(
                job_id=job.id,
                stage_key="failed",
                stage_label="Workflow failed",
                status="failed",
                summary=str(exc),
            )
        except KeyError:
            return None
        store.log_api_usage(
            user_id=job.user_id,
            endpoint="analysis.worker.failed",
            provider=os.getenv("TRADINGAGENTS_LLM_PROVIDER"),
            model=os.getenv("TRADINGAGENTS_DEEP_THINK_LLM") or os.getenv("TRADINGAGENTS_QUICK_THINK_LLM"),
        )
        return failed


def maybe_run_scheduled_security_master_sync(*args, store=None, now=None, sync_func=None) -> bool:
    if args:
        store = args[0]
    if store is None:
        raise TypeError("store is required")
    if not is_security_master_auto_sync_enabled():
        return False
    now = now or datetime.now(timezone.utc)
    if now.weekday() != 0 or now.hour != 0:
        return False
    latest_run = store.latest_security_master_sync_run()
    if latest_run and latest_run.finished_at and latest_run.finished_at.date() == now.date():
        return False
    (sync_func or sync_security_master)(store)
    return True


def run_worker_loop(*, poll_interval_seconds: float = 1.0) -> None:
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("ALPHAPILOT_DATABASE_URL is required for the worker")
    store = SqlAlchemyAlphaPilotStore(database_url)
    engine = AnalysisEngineService()
    queue = RedisAnalysisQueue(get_redis_url())
    while True:
        maybe_run_scheduled_security_master_sync(store)
        job_id = queue.dequeue(timeout_seconds=5)
        if job_id:
            process_analysis_job(store=store, engine=engine, job_id=job_id)
        else:
            time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    run_worker_loop()
