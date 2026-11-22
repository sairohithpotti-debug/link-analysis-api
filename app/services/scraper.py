from dataclasses import dataclass
import re
from bs4 import BeautifulSoup
import httpx

from app.services.url_validator import SSRFValidationError, validate_public_url


NOISE_TAGS = {"script", "style", "noscript", "svg", "canvas", "iframe", "form", "footer", "nav"}
MAX_REDIRECTS = 5
MAX_CHARS = 14000


@dataclass
class ExtractedPage:
    source_url: str
    final_url: str
    title: str
    meta_description: str
    headings: list[str]
    cleaned_text: str


async def fetch_and_clean_page(url: str, timeout_seconds: float = 15.0) -> ExtractedPage:
    current_url = validate_public_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; LinkAnalysisBot/1.0; +https://example.com/bot)",
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout_seconds),
        follow_redirects=False,
        headers=headers,
    ) as client:
        response = None
        for _ in range(MAX_REDIRECTS + 1):
            resp = await client.get(current_url)
            if resp.is_redirect or resp.status_code in {301, 302, 303, 307, 308}:
                location = resp.headers.get("location")
                if not location:
                    raise SSRFValidationError("Redirect response missing Location header.")
                next_url = str(resp.url.join(location))
                current_url = validate_public_url(next_url)
                continue
            response = resp
            break

        if response is None:
            raise SSRFValidationError("Exceeded maximum allowed redirects.")

        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = (soup.title.string.strip() if soup.title and soup.title.string else "").strip()
    meta_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    meta_description = (meta_tag.get("content", "") if meta_tag else "").strip()

    headings: list[str] = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        text = re.sub(r"\s+", " ", h.get_text(" ", strip=True)).strip()
        if text and text not in headings:
            headings.append(text)
    headings = headings[:25]

    for tag in soup.find_all(list(NOISE_TAGS)):
        tag.decompose()

    main_container = soup.find("main") or soup.find("article") or soup.body or soup
    raw_lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in main_container.get_text("\n", strip=True).splitlines()
    ]
    deduped_lines: list[str] = []
    seen = set()
    for line in raw_lines:
        if len(line) < 2:
            continue
        key = line.lower()
        if key not in seen:
            seen.add(key)
            deduped_lines.append(line)

    cleaned_text = "\n".join(deduped_lines)[:MAX_CHARS]

    return ExtractedPage(
        source_url=url,
        final_url=str(response.url),
        title=title,
        meta_description=meta_description,
        headings=headings,
        cleaned_text=cleaned_text,
    )
