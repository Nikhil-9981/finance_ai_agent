import requests
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup

# Optionally use sec-edgar-api if installed
try:
    from sec_edgar_api import EdgarClient
    HAVE_EDGAR_CLIENT = True
except ImportError:
    HAVE_EDGAR_CLIENT = False

 
logger = logging.getLogger("scraper_agent")

app = FastAPI(title="Scraper Agent – SEC Filings")

class FilingRequest(BaseModel):
    cik: str
    filing_type: str = "10-K"

class FilingResponse(BaseModel):
    cik: str
    filing_type: str
    document_text: str

def fetch_with_python_loader(cik, filing_type):
    """
    Try to fetch the latest filing using the sec-edgar-api Python loader.
    Returns the document text if successful, else None.
    """
    if not HAVE_EDGAR_CLIENT:
        logger.warning("sec-edgar-api not installed; skipping Python loader.")
        return None

    try:
        edgar = EdgarClient(user_agent="finance-assistant-bot (rathaurnikhil14@gmail.com)")
        logger.info("Trying sec-edgar-api Python loader...")
        submissions = edgar.get_submissions(cik=cik)
        filings = submissions.get("filings", {}).get("recent", {})
        if not filings:
            logger.warning("No recent filings from sec-edgar-api loader.")
            return None
        accession_numbers = filings.get("accessionNumber", [])
        form_types = filings.get("form", [])
        primary_docs = filings.get("primaryDocument", [])
        for acc, ftype, doc in zip(accession_numbers, form_types, primary_docs):
            if ftype.upper() == filing_type.upper():
                clean_cik = cik.lstrip("0")
                acc_nodash = acc.replace("-", "")
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{clean_cik}/{acc_nodash}/{doc}"
                logger.info(f"Found {filing_type} via sec-edgar-api loader: {filing_url}")
                filing_resp = requests.get(filing_url, headers={"User-Agent": "finance-assistant-bot (rathaurnikhil14@gmail.com)"}, timeout=300)
                if filing_resp.status_code == 200:
                    return filing_resp.text[:50000]
                else:
                    logger.warning(f"Failed to fetch doc from {filing_url} (loader)")
        logger.warning("Requested filing type not found with sec-edgar-api loader.")
        return None
    except Exception as e:
        logger.error(f"sec-edgar-api loader failed: {e}")
        return None

def fetch_with_edgar_api(cik, filing_type):
    """
    Tries to fetch the latest filing using SEC's new JSON API.
    Returns the full filing text if found, else None.
    """
    base_url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    headers = {"User-Agent": "finance-assistant-bot (youremail@example.com)"}
    logger.info(f"Trying SEC EDGAR JSON API: {base_url}")
    try:
        resp = requests.get(base_url, headers=headers, timeout=100)
        if resp.status_code != 200:
            logger.warning(f"SEC EDGAR JSON API request failed: {resp.status_code}")
            return None

        data = resp.json()
        filings = data.get("filings", {}).get("recent", {})
        if not filings:
            logger.warning("No recent filings found in JSON API.")
            return None

        accession_numbers = filings.get("accessionNumber", [])
        form_types = filings.get("form", [])
        primary_docs = filings.get("primaryDocument", [])

        for acc, ftype, doc in zip(accession_numbers, form_types, primary_docs):
            if ftype.upper() == filing_type.upper():
                clean_cik = cik.lstrip("0")
                acc_nodash = acc.replace("-", "")
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{clean_cik}/{acc_nodash}/{doc}"
                logger.info(f"Found {filing_type} filing via JSON API: {filing_url}")
                filing_resp = requests.get(filing_url, headers=headers, timeout=100)
                if filing_resp.status_code == 200:
                    text = filing_resp.text[:50000]
                    return text
                else:
                    logger.warning(f"Failed to fetch filing doc from {filing_url}")
        logger.warning("Requested filing type not found in JSON API.")
        return None
    except Exception as e:
        logger.error(f"Error using SEC EDGAR JSON API: {e}")
        return None

def fetch_with_atom_feed(cik, filing_type):
    """
    Fallback: Fetches the latest filing using the old Atom feed + BeautifulSoup.
    """
    feed_url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&CIK={cik}"
        f"&type={filing_type}&owner=exclude&count=1&output=atom"
    )
    headers = {"User-Agent": "finance-assistant-bot (youremail@example.com)"}
    logger.info(f"Trying Atom feed: {feed_url}")
    feed_resp = requests.get(feed_url, headers=headers, timeout=100)
    if feed_resp.status_code != 200:
        logger.error(f"Failed to fetch EDGAR feed: {feed_resp.status_code}")
        raise HTTPException(502, "Failed to fetch EDGAR feed")

    soup = BeautifulSoup(feed_resp.content, "xml")
    entry = soup.find("entry")
    if not entry:
        logger.error("No filings found for this CIK/type in Atom feed.")
        raise HTTPException(404, "No filings found for this CIK/type")

    link_tag = entry.find("link", {"rel": "alternate"})
    if not link_tag or not link_tag.get("href"):
        logger.error("Malformed EDGAR feed entry (no filing link).")
        raise HTTPException(502, "Malformed EDGAR feed entry")
    doc_url = link_tag["href"]
    logger.info(f"Found filing link via Atom feed: {doc_url}")

    doc_resp = requests.get(doc_url, headers=headers, timeout=100)
    if doc_resp.status_code != 200:
        logger.error(f"Failed to fetch filing document: {doc_resp.status_code}")
        raise HTTPException(502, "Failed to fetch filing document")

    doc_soup = BeautifulSoup(doc_resp.content, "html.parser")
    text = doc_soup.get_text(separator="\n")
    snippet = text[:50000]
    return snippet

@app.post("/filing", response_model=FilingResponse)
async def get_filing(req: FilingRequest):
    logger.info(f"Request: CIK={req.cik}, Filing Type={req.filing_type}")

    # 1. Try sec-edgar-api Python loader (super simple)
    text = fetch_with_python_loader(req.cik, req.filing_type)
    if text:
        logger.info("Success using sec-edgar-api Python loader.")
        return FilingResponse(
            cik=req.cik,
            filing_type=req.filing_type,
            document_text=text
        )

    # 2. Try SEC EDGAR JSON API
    text = fetch_with_edgar_api(req.cik, req.filing_type)
    if text:
        logger.info("Success using SEC EDGAR JSON API.")
        return FilingResponse(
            cik=req.cik,
            filing_type=req.filing_type,
            document_text=text
        )

    # 3. Fallback: Atom feed + BeautifulSoup
    logger.warning("Both sec-edgar-api loader and JSON API failed. Falling back to Atom feed.")
    text = fetch_with_atom_feed(req.cik, req.filing_type)
    logger.info("Success using Atom feed fallback.")
    return FilingResponse(
        cik=req.cik,
        filing_type=req.filing_type,
        document_text=text
    )
