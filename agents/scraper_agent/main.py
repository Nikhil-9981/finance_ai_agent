# agents/scraper_agent/main.py

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup

app = FastAPI(title="Scraper Agent – SEC Filings")

class FilingRequest(BaseModel):
    cik: str
    filing_type: str = "10-K"

class FilingResponse(BaseModel):
    cik: str
    filing_type: str
    document_text: str

@app.post("/filing", response_model=FilingResponse)
async def get_filing(req: FilingRequest):
    # 1) Fetch the latest filing RSS feed from SEC EDGAR
    feed_url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&CIK={req.cik}"
        f"&type={req.filing_type}&owner=exclude&count=1&output=atom"
    )
    headers = {"User-Agent": "finance-assistant-bot (youremail@example.com)"}
    feed_resp = requests.get(feed_url, headers=headers)
    if feed_resp.status_code != 200:
        raise HTTPException(502, "Failed to fetch EDGAR feed")

    soup = BeautifulSoup(feed_resp.content, "xml")
    entry = soup.find("entry")
    if not entry:
        raise HTTPException(404, "No filings found for this CIK/type")

    # 2) Extract link to full filing
    link_tag = entry.find("link", {"rel": "alternate"})
    if not link_tag or not link_tag.get("href"):
        raise HTTPException(502, "Malformed EDGAR feed entry")
    doc_url = link_tag["href"]

    # 3) Download and parse the filing HTML
    doc_resp = requests.get(doc_url, headers=headers)
    if doc_resp.status_code != 200:
        raise HTTPException(502, "Failed to fetch filing document")

    doc_soup = BeautifulSoup(doc_resp.content, "html.parser")
    text = doc_soup.get_text(separator="\n")
    # Limit size to first 50k chars to keep payload reasonable
    snippet = text[:50_000]

    return FilingResponse(
        cik=req.cik,
        filing_type=req.filing_type,
        document_text=snippet
    )
