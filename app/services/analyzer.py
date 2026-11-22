import os
from google import genai
from google.genai import types

from app.schemas import LinkAnalysisResponse
from app.services.scraper import ExtractedPage


SYSTEM_INSTRUCTION = """You are a senior digital marketing, SEO, and competitive intelligence analyst.
Analyze the provided website extraction carefully and return strictly structured JSON matching the schema.

Rules:
1. Ground claims in the extracted website content first. Clearly mark any inferred services with `is_inferred: true`.
2. In Section 1, identify at least 3 realistic competitors when reliable market/industry information can be determined from the page.
3. In Section 2, return exactly 5 high-value target search queries across Google Search, Facebook, Instagram, LinkedIn, and X (Twitter) — do not invent numeric search volumes.
4. In Section 3, provide primary, secondary, long-tail, and business keywords, an SEO title, a meta description, and supporting content ideas.
5. In Section 4, list the top 5 services with description, target industry, target customer, main benefit, and `is_inferred`.
6. In Section 5, identify primary/secondary audiences, industry segments, business types, customer profiles, location (if available), needs/challenges, interests, and marketing segments.
"""


def _build_prompt(page: ExtractedPage) -> str:
    headings_block = "\n".join(f"- {h}" for h in page.headings) or "None extracted"
    return f"""Analyze this website:
Source URL: {page.source_url}
Final URL: {page.final_url}
Page Title: {page.title or "N/A"}
Meta Description: {page.meta_description or "N/A"}

Key Headings:
{headings_block}

Cleaned Page Content:
{page.cleaned_text}
"""


async def analyze_website_content(page: ExtractedPage) -> LinkAnalysisResponse:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    primary_model = os.getenv("PRIMARY_MODEL", "gemini-3.8-flash")
    fallback_model = os.getenv("FALLBACK_MODEL", "gemini-3.5-flash-lite")
    client = genai.Client(api_key=api_key)
    prompt = _build_prompt(page)

    last_error: Exception | None = None
    for model_name in (primary_model, fallback_model):
        try:
            config_kwargs = {
                "system_instruction": SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
                "response_schema": LinkAnalysisResponse,
            }
            if model_name.startswith("gemini-3."):
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="LOW")

            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            if response.parsed is not None:
                parsed = LinkAnalysisResponse.model_validate(response.parsed)
                parsed.source_url = page.source_url
                parsed.final_url = page.final_url
                parsed.model_used = model_name
                return parsed

            if response.text:
                parsed = LinkAnalysisResponse.model_validate_json(response.text)
                parsed.source_url = page.source_url
                parsed.final_url = page.final_url
                parsed.model_used = model_name
                return parsed
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(
        f"LLM analysis failed across models ({primary_model}, {fallback_model}): {last_error}"
    )
