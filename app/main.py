import os
from fastapi import FastAPI, HTTPException, status
import httpx

from app.schemas import LinkAnalysisRequest, LinkAnalysisResponse
from app.services.analyzer import analyze_website_content
from app.services.scraper import fetch_and_clean_page
from app.services.url_validator import SSRFValidationError


app = FastAPI(
    title="AI-Powered Website Link Analysis API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/link-analysis",
    response_model=LinkAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def link_analysis(payload: LinkAnalysisRequest) -> LinkAnalysisResponse:
    try:
        extracted = await fetch_and_clean_page(str(payload.url))
        return await analyze_website_content(extracted)
    except SSRFValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or blocked URL: {exc}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch target URL: {exc}",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
