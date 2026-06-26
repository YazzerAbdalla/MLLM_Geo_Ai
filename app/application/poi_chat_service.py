import hashlib
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
TOP_CATEGORIES_LIMIT = 15
CACHE_TTL = 3600
REQUIRED_ANALYSIS_FIELDS = ["total_pois", "area_km2", "poi_density", "top_categories"]

GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=0.2,
    max_output_tokens=1024,
)

SYSTEM_PROMPT = (
    "You are an experienced Urban Planning Consultant specializing in GIS, "
    "land-use analysis, and Point of Interest (POI) interpretation.\n\n"
    "Your role is to help users understand urban areas, identify patterns, "
    "evaluate opportunities, and explain what the available POI data suggests.\n"
    "Think like a city planner rather than a database.\n\n"
    "Always distinguish between:\n"
    "• Facts directly supported by the supplied POI data.\n"
    "• Reasonable professional inferences drawn from those facts.\n"
    "• Information that cannot be determined without additional datasets.\n\n"
    "Base every answer primarily on the supplied POI analysis.\n"
    "Use professional urban planning reasoning to interpret the available information.\n"
    "You may draw reasonable conclusions from the observed POI distribution.\n\n"
    "When evaluating an area, consider:\n"
    "• Which categories dominate and which are missing\n"
    "• POI density and diversity of land use\n"
    "• Concentration of services\n"
    "• What complementary businesses would fit the existing ecosystem\n\n"
    "When the user asks about suitability, opportunities, or recommendations:\n"
    "• Explain what the current POI distribution suggests\n"
    "• Identify complementary business opportunities based on observed clusters\n"
    "• Compare categories internally within the analyzed area\n"
    "• Never guarantee success or predict profit\n\n"
    "When information is limited:\n"
    "• First explain what CAN be concluded\n"
    "• Then explain the reasoning\n"
    "• Then state what additional information would improve confidence\n\n"
    "Speak naturally as an experienced urban planning consultant.\n"
    "Be professional but conversational.\n"
    "Use short paragraphs.\n"
    "Avoid repeating all statistics in every answer — only mention numbers when relevant.\n"
    "Do not mention that you are an AI.\n"
    "Do not output JSON or markdown code blocks.\n\n"
    "Safety rules — NEVER do the following:\n"
    "• Invent POIs, statistics, population, traffic, competition, or customer demand\n"
    "• Claim certainty when the data only supports an inference\n"
    "• Fabricate any information not present in the supplied analysis"
)


class GeminiConfigError(RuntimeError):
    pass


class GeminiTimeoutError(RuntimeError):
    pass


class GeminiRateLimitError(RuntimeError):
    pass


class GeminiInvalidRequestError(RuntimeError):
    pass


class GeminiApiError(RuntimeError):
    pass


_summary_cache: Dict[str, Dict[str, Any]] = {}


def _get_cached_summary(analysis_hash: str) -> Optional[str]:
    entry = _summary_cache.get(analysis_hash)
    if entry is None:
        return None
    if time.time() - entry["created_at"] > CACHE_TTL:
        del _summary_cache[analysis_hash]
        return None
    return entry["summary"]


def _set_cached_summary(analysis_hash: str, summary: str) -> None:
    _summary_cache[analysis_hash] = {
        "summary": summary,
        "created_at": time.time(),
    }


def _analysis_hash(analysis: dict) -> str:
    raw = json.dumps(analysis, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _limit_history(history: List[dict]) -> List[dict]:
    MAX_MESSAGES = 10
    MAX_CHARS = 8000

    limited: List[dict] = []
    total_chars = 0

    for msg in reversed(history):
        role = msg.get("role", "")
        content = msg.get("content", "")
        msg_chars = len(role) + len(content) + 5

        if len(limited) >= MAX_MESSAGES:
            break
        if total_chars + msg_chars > MAX_CHARS:
            break

        limited.insert(0, msg)
        total_chars += msg_chars

    return limited


def build_analysis_block(analysis: dict) -> str:
    total_pois = analysis.get("total_pois", "N/A")
    area_km2 = analysis.get("area_km2", "N/A")
    poi_density = analysis.get("poi_density", "N/A")

    top_categories = analysis.get("top_categories", [])[:TOP_CATEGORIES_LIMIT]
    category_counts = analysis.get("category_counts", {})
    limited_counts = dict(
        sorted(category_counts.items(), key=lambda x: -x[1])[:TOP_CATEGORIES_LIMIT]
    )
    reverse_geocoding = analysis.get("reverse_geocoding")

    block = "--- POI Analysis Data ---\n"
    block += f"Total POIs: {total_pois}\n"
    block += f"Area (km²): {area_km2}\n"
    block += f"POI Density (per km²): {poi_density}\n"
    block += (
        f"Top Categories: {json.dumps(top_categories, ensure_ascii=False)}\n"
    )
    block += (
        f"Category Counts: {json.dumps(limited_counts, ensure_ascii=False)}\n"
    )

    if reverse_geocoding:
        area_name = reverse_geocoding.get("area_name")
        if area_name:
            block += f"Location: {area_name}\n"

    return block


def build_history_block(history: List[dict]) -> str:
    if not history:
        return ""
    block = "--- Previous Conversation ---\n"
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        block += f"{role}: {content}\n"
    return block


def build_chat_prompt(
    analysis: dict,
    history: Optional[List[dict]] = None,
    question: str = "",
    include_summary: bool = True,
) -> str:
    analysis_block = build_analysis_block(analysis)
    history_block = build_history_block(history or [])

    if include_summary:
        return (
            f"{SYSTEM_PROMPT}\n\n"
            f"{analysis_block}\n\n"
            f"{history_block}\n"
            f"User Question: {question}\n\n"
            "Based on the POI analysis and the user's question above:\n\n"
            "First, write a brief 1-2 sentence summary of the area.\n"
            "Start directly with what the area contains.\n"
            "Avoid phrases like 'The selected area covers' or 'This analysis indicates'.\n\n"
            "Then answer the user's question using your urban planning expertise.\n"
            "Provide useful insights about what the POI distribution suggests.\n\n"
            "Use this format:\n"
            "Summary:\n"
            "<summary>\n\n"
            "Answer:\n"
            "<answer>"
        )

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"{analysis_block}\n\n"
        f"{history_block}\n"
        f"User Question: {question}\n\n"
        "Answer the user's question based on the supplied POI analysis. "
        "Provide useful urban planning insights where the data supports them."
    )


def _parse_summary_answer(raw: str) -> tuple[str, str]:
    summary = ""
    answer = ""

    m = re.search(r"Summary:\s*(.*?)(?=\n\s*Answer:|\Z)", raw, re.DOTALL | re.IGNORECASE)
    if m:
        summary = m.group(1).strip()

    m = re.search(r"Answer:\s*(.*)", raw, re.DOTALL | re.IGNORECASE)
    if m:
        answer = m.group(1).strip()

    if not answer and summary:
        answer = summary
    elif not answer:
        answer = raw.strip()

    return summary, answer


_RETRYABLE_KEYWORDS = ["timeout", "unavailable", "429", "rate limit", "too many requests"]


def _is_retryable(exception: Exception) -> bool:
    msg = str(exception).lower()
    return any(kw in msg for kw in _RETRYABLE_KEYWORDS)


def _map_to_custom_exception(e: Exception) -> RuntimeError:
    msg = str(e).lower()
    if "api key" in msg:
        return GeminiConfigError(str(e))
    if "timeout" in msg or "deadline" in msg:
        return GeminiTimeoutError(str(e))
    if "429" in msg or "rate" in msg:
        return GeminiRateLimitError(str(e))
    if "invalid" in msg or "bad request" in msg:
        return GeminiInvalidRequestError(str(e))
    return GeminiApiError(str(e))


def _call_gemini(api_key: str, prompt: str) -> str:
    client = genai.Client(api_key=api_key)

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=GENERATION_CONFIG,
            )
            return response.text
        except Exception as e:
            if attempt == 0 and _is_retryable(e):
                time.sleep(1)
                continue
            raise _map_to_custom_exception(e) from e

    raise GeminiApiError("Gemini call failed after retry")  # pragma: no cover


def chat_with_poi_analysis(
    analysis: dict,
    question: str,
    history: Optional[List[dict]] = None,
) -> dict:
    if not GEMINI_API_KEY:
        raise GeminiConfigError("GEMINI_API_KEY is not configured")

    for field in REQUIRED_ANALYSIS_FIELDS:
        if field not in analysis:
            raise GeminiInvalidRequestError(
                f"Invalid analysis payload: missing required field '{field}'"
            )

    history = _limit_history(history or [])

    analysis_key = _analysis_hash(analysis)
    cached_summary = _get_cached_summary(analysis_key)

    prompt_start = time.perf_counter()

    if cached_summary is not None:
        prompt = build_chat_prompt(
            analysis, history, question, include_summary=False
        )
        prompt_time = time.perf_counter() - prompt_start

        gemini_start = time.perf_counter()
        raw = _call_gemini(GEMINI_API_KEY, prompt)
        gemini_time = time.perf_counter() - gemini_start

        summary = cached_summary
        answer = raw
        summary_reused = True
    else:
        prompt = build_chat_prompt(
            analysis, history, question, include_summary=True
        )
        prompt_time = time.perf_counter() - prompt_start

        gemini_start = time.perf_counter()
        raw = _call_gemini(GEMINI_API_KEY, prompt)
        gemini_time = time.perf_counter() - gemini_start

        summary, answer = _parse_summary_answer(raw)

        _set_cached_summary(analysis_key, summary)
        summary_reused = False

    logger.info(
        "POI chat | model=%s prompt_ms=%.1f gemini_ms=%.1f history=%d q_len=%d summary_reused=%s",
        GEMINI_MODEL,
        round(prompt_time * 1000, 1),
        round(gemini_time * 1000, 1),
        len(history),
        len(question),
        summary_reused,
    )

    return {
        "summary": summary,
        "answer": answer,
        "model": GEMINI_MODEL,
    }
