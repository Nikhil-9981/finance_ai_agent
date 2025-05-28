<a id="readme-top"></a>

<!-- Project Header -->
<div align="center">
  <h1>Finance AI Agent: Multi-Agent Market Intelligence Platform</h1>
  <p>
    <strong>Real-time financial insights using LLMs, vector DBs, market APIs, and SEC filings.</strong>
  </p>
</div>

---

## 🚀 Table of Contents

- [About The Project](#about-the-project)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running Locally](#running-locally)
- [API Endpoints](#api-endpoints)
- [Deployment](#deployment)
- [Testing](#testing)
- [Known Issues and Limitations](#known-issues-and-limitations)
- [Roadmap & Future Improvements](#roadmap--future-improvements)
- [Contact](#contact)

---

## About The Project

**Finance AI Agent** is an open multi-agent platform for financial intelligence.  
It combines **real-time and historical market data**, **LLM-based question answering**, **vector retrieval**, and **SEC filings scraping**—all orchestrated by FastAPI microservices and a Streamlit frontend.

**Sample Use-Cases:**
- "What’s our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
- "Summarize the latest 10-K filing for AAPL."
- "Show me price history and company info for TSLA, AMZN."

---

## Architecture

[Streamlit UI] <--> [Orchestrator Agent] <==> [API Agent] (Market Data)
<==> [Scraper Agent] (SEC Filings)
<==> [Retriever Agent] (Vector DB/FAISS)
<==> [Language Agent] (LLM/RAG)
<==> [Voice Agent] (STT/TTS)



- **Streamlit Frontend:** User interface for both text and (optionally) voice input.
- **Orchestrator Agent:** Coordinates requests, extracts tickers, triggers other agents.
- **API Agent:** Fetches quotes, OHLCV, company info, financials, dividends via AlphaVantage & yFinance.
- **Scraper Agent:** Retrieves SEC filings using Edgar/BeautifulSoup/sec-edgar-api.
- **Retriever Agent:** Pulls relevant knowledge base/context from FAISS vector store.
- **Language Agent:** Synthesizes market briefs using a hosted LLM (Groq Llama-3, etc.).
- **Voice Agent:** (Optional) Speech-to-text and text-to-speech for voice queries.
- **Celery/Redis:** Used for background tasks like periodic FAISS index updates.

---

## Key Features

- **Natural Language Q&A:** Ask complex market/portfolio questions and get concise answers.
- **Automatic Symbol/CIK Extraction:** Dynamically extracts relevant tickers from questions.
- **Multi-Agent Orchestration:** Pluggable, modular design for easy scaling.
- **Real-Time & Historical Data:** API Agent fetches the latest price, OHLCV, and financials.
- **SEC Filings Integration:** Scraper Agent fetches and summarizes filings (10-K, 20-F, etc.).
- **Voice Mode (Optional):** End-to-end pipeline: speech → answer → speech (uses pyttsx3/sphinx).
- **Easy Deployment:** Ready for local use or Render/Cloud deployment.
- **Celery Cronjobs:** Automatic FAISS index refresh for new documents.

---

## Getting Started

### Prerequisites

- Python 3.9+
- [Render.com](https://render.com/) account (for deployment)
- Git, pip, and basic terminal access
- API keys for:
  - **AlphaVantage** (`ALPHA_VANTAGE_API_KEY`)
  - **Groq** (`GROQ_API_KEY`)
  - (optional) SEC Edgar API, yFinance requires no API key

### Installation

#### 1. Clone the Repo

```bash
git clone https://github.com/YOUR_GITHUB/finance-ai-agent.git
cd finance-ai-agent


2. Set Up Virtual Environment

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


3. Environment Variables

Create a .env in the root or in each agent’s folder as needed:



ALPHA_VANTAGE_API_KEY=your_key
GROQ_API_KEY=your_key
ORCHESTRATOR_AGENT_URL=https://your-orchestrator-url.onrender.com/orchestrate
API_AGENT_URL=https://your-api-agent-url.onrender.com/quote
SCRAPER_AGENT_URL=https://your-scraper-agent-url.onrender.com/filing
RETRIEVER_AGENT_URL=https://your-retriever-agent-url.onrender.com/retrieve
LANGUAGE_AGENT_URL=https://your-language-agent-url.onrender.com/analyze_graph
VOICE_AGENT_URL=https://your-voice-agent-url.onrender.com/voice_brief
VOICE_TTS_URL=https://your-voice-agent-url.onrender.com/tts

```

Run Locally

Each agent is a FastAPI app. Example for API Agent:

uvicorn agents.api_agent.main:app --host 0.0.0.0 --port 8001
uvicorn agents.api_agent.main:app --port 8001 
uvicorn agents.scraper_agent.main:app --port 8002 
uvicorn agents.retriever_agent.main:app --port 8003 
uvicorn agents.language_agent.main:app --port 8004 
uvicorn agents.voice_agent.main:app --port 8005 
uvicorn agents.orchestrator_agent.main:app --port 8006 

Streamlit Frontend:

streamlit run stream_app/main.py



API Endpoints

(For full OpenAPI docs, run any FastAPI agent and visit /docs!)

    API Agent: /quote — POST — market data, prices, info, historicals

    Scraper Agent: /filing — POST — fetch latest SEC filings for a CIK/type

    Retriever Agent: /retrieve — POST — fetch relevant text chunks from FAISS KB

    Language Agent: /analyze_graph — POST — generate answer from question/context
    /extract_symbols — POST — extract tickers from question

    Voice Agent: /voice_brief — POST (audio in, audio out); /tts — POST (text to mp3)

    Orchestrator Agent: /orchestrate — POST — main entry for frontend





 Deployment
Recommended: Render.com

Each agent gets its own Web Service on Render.

Steps:

    Push code to GitHub.

    For each agent:

        Go to Render dashboard, click “New +”, select “Web Service.”

        Point to the repo/subfolder, set the build/start commands:

            Build: pip install -r requirements.txt

            Start: uvicorn main:app --host 0.0.0.0 --port 10000 (change port as desired)

        Set environment variables (API keys, service URLs, etc.).

    After all agents are deployed, update each agent’s .env or config to use the public Render URLs (not localhost).

    Deploy Streamlit frontend last, pointing to your orchestrator’s public endpoint.

Troubleshooting:
If you see “Connection Refused” errors, check that the service URLs are not pointing to localhost and that all dependent agents are up and running.
Testing

    Each FastAPI agent exposes /ping or /docs for quick testing.

    Use curl or Postman to test each endpoint before integrating end-to-end.

    Example:
    curl https://api-agent-xxxxx.onrender.com/quote \
  -H "Content-Type: application/json" \
  -d '{"symbols":["TSM"],"history":true,"info":true}'
 


 Known Issues and Limitations

    Voice Mode:
    Voice agent works offline (pyttsx3 + sphinx) and accuracy varies. For deployment, consider switching to cloud TTS (e.g., ElevenLabs, Google TTS) for clearer speech.

    Latency:
    LLM calls and multi-agent pipeline can be slow, especially on free Render plans.

    Testing:
    More test functions and integration tests are recommended for robustness.

    Symbol/CIK Extraction:
    Ticker/CIK extraction is AI-driven, but not always perfect—can be improved by using mapping tables or APIs.

    Deployment:
    All agents must be running and accessible to each other via public URLs. Localhost URLs will NOT work in cloud deployment.

    Voice Input:
    Voice pipeline may fail or be inaccurate; for demo, prefer text input.
    More optimization possible for STT/TTS and error handling.

    Feature Gaps:

        Could not complete advanced testing and code optimization due to time limits.

        Working on video demonstration for future improvement.

Roadmap & Future Improvements

Add more test functions for all agents and end-to-end flows.

Switch voice pipeline to use cloud-based TTS for production.

Further optimize API latency and multi-agent orchestration.

Add more coverage for ETFs, global stocks, and CIK/ticker lookup tables.

Add monitoring/logging dashboards for easier debugging.

    Video Demo: Work in progress, will be shared soon.

Contact

Nikhil Kumar Singh
LinkedIn
Email: rathaurnikhil14@gmail.com
Project Link: https://github.com/Nikhil-9981/Finance_AI_agent
<div align="center"> <h2>THANK YOU!</h2> <p>Your time and attention mean the world! ✨</p> </div> <p align="right">(<a href="#readme-top"><strong>Back to top</strong></a>)</p> ```