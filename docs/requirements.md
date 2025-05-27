# Requirements & User Stories

**Deadline:** 29 May 2025, 18:00 IST

---

## 1. Use Case

Every trading day at **08:00** local time, the portfolio manager asks via voice:
> “What’s our risk exposure in Asia tech stocks today, and highlight any earnings surprises?”

System must respond **verbally** and also display text fallback:
> “Today, your Asia tech allocation is 22 % of AUM, up from 18 % yesterday.  
TSMC beat estimates by 4 %, Samsung missed by 2 %. Regional sentiment is neutral with a cautionary tilt due to rising yields.”

---

## 2. Functional Requirements

| ID   | Description                                                                                       |
|------|---------------------------------------------------------------------------------------------------|
| FR1  | **Schedule**: Trigger daily at 08:00 via orchestrator                                              |
| FR2  | **API Agent**: Fetch real-time & historical prices from AlphaVantage (primary) and yfinance         |
| FR3  | **Scraper Agent**: Download & parse SEC filings via EDGAR API and BeautifulSoup                    |
| FR4  | **Embedding**: Chunk documents & embed with sentence-transformers into FAISS                        |
| FR5  | **Retriever Agent**: Return top-k relevant text chunks + confidence score                          |
| FR6  | **Analysis Agent**: Compute Asia-tech % of AUM (today vs. yesterday) and earnings‐surprise metrics  |
| FR7  | **Language Agent**: Generate concise narrative via LangGraph/CrewAI using retrieved chunks         |
| FR8  | **Voice Agent**:  
> • STT: Whisper on incoming audio  
> • TTS: Coqui-TTS for outgoing narrative  
| FR9  | **Streamlit UI**:  
> • Record & play audio  
> • Display text fallback & basic charts  
| FR10 | **Fallback**: If retriever confidence < threshold, voice-prompt for clarification                   |
| FR11 | **Deployment**: Containerize (Docker + docker-compose) and deploy a live Streamlit app              |
| FR12 | **Logging**: Record all AI-tool prompts, responses, and parameters in `docs/ai_tool_usage.md`       |

---

## 3. Non-Functional Requirements

- **Latency:** Total round-trip (audio in → audio out) < 5 seconds  
- **Reliability:** ≥ 99% uptime during market hours  
- **Test Coverage:** ≥ 80% unit & integration tests  
- **Documentation:** Full setup, deployment, and AI-usage transparency  
- **Modularity:** Each agent is an independent FastAPI microservice  

---

## 4. User Stories & Acceptance Criteria

### US1: Morning Market Brief via Voice  
**As** a portfolio manager  
**I want** to say “Morning Market Brief” in the Streamlit app at 08:00  
**So that** I get an audible summary of Asia-tech exposure and earnings surprises.

- **AC1.1** STT correctly transcribes the wake phrase  
- **AC1.2** System triggers data pipeline automatically at 08:00  
- **AC1.3** TTS reads out the accurate narrative  

### US2: Text Fallback  
**As** a portfolio manager  
**I want** the brief also displayed as text  
**So that** I can review or copy key figures.

- **AC2.1** Narrative text appears in the UI within 3 seconds  
- **AC2.2** Charts show allocation % and surprise figures  

### US3: Clarification Fallback  
**As** a user  
**I want** the system to ask follow-up questions if unsure  
**So that** I can refine my query.

- **AC3.1** If retriever confidence < 0.6, system asks “Did you mean…?”  
- **AC3.2** New input restarts the pipeline  

---

