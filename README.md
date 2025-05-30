<a id="readme-top"></a>

<!-- Project Header -->
<div align="center">
  <h1>Finance AI Agent: Multi-Agent Market Intelligence Platform</h1>
  <p>
    <strong>Real-time financial insights using LLMs, vector DBs, market APIs, and SEC filings.</strong>
  </p>
</div>
  
 

**Video_url = https://drive.google.com/file/d/1XBixKRdV0ExpVJsHXe4B-BUEio4FdmcB/view?usp=sharing**


## Live Demo Screenshot

![Demo Screenshot](https://github.com/Nikhil-9981/finance_ai_agent/blob/main/WhatsApp%20Image%202025-05-30%20at%2018.03.29.jpeg?raw=true)



## ⚠️ Deployment & Feature Notes

**Note :- Still working o nthe porject , Will complete by today night.**

- 🚀 **Deployment Status**  
  The main application is deployed and accessible at the following URLs:

- [Orchestrator Agent](https://finance-ai-agent-rfqw.onrender.com/orchestrate)
- [API Agent (Instance 1)](https://finance-ai-agent-tnjq.onrender.com)
- [Scraper Agent (Instance 2)](https://finance-ai-agent-1.onrender.com)
- [Retriever Agent](https://retriever-agent.onrender.com/retrieve)
- [Language Agent](https://finance-ai-agent-rqd6.onrender.com/analyze_graph)
- [Voice Agent - Voice Brief](https://finance-ai-agent-1-u7bk.onrender.com/voice_brief)
- [Voice Agent - TTS](https://finance-ai-agent-1-u7bk.onrender.com/tts)

- 
- 🧠 **Retriever API (FAISS Agent)**  
  - The FAISS-based retriever agent is under development and currently hosted at:  
    [Retriever Agent](https://retriever-agent.onrender.com)  
  - Due to the increasing size of the retriever index, the API is facing issues on free-tier hosting. This is being worked on and will be resolved **by end of day today**.

- 📄 **Documentation Update**  
  Some parts of the documentation are currently incomplete due to time constraints. These will be updated soon to fully reflect all features and usage instructions.

- 🎙️ **Speech Functionality**  
  - **Text-to-microphone (speech-to-text)** is in progress.  
  - **Text-to-speech** functionality is **not yet integrated**, and may cause minor runtime issues during interaction.  
  - Both features are under active development and will be addressed in the upcoming deployment update.

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

# Finance AI Agent

![Architecture Diagram](https://github.com/Nikhil-9981/finance_ai_agent/blob/main/deepseek_mermaid_20250530_d0ac87.png?raw=true)

An AI-driven multi-agent system for financial data analysis...



- **Streamlit Frontend:** User interface for both text and (optionally) voice input.
- **Orchestrator Agent:** Coordinates requests, extracts tickers, triggers other agents.
- **API Agent:** Fetches quotes, OHLCV, company info, financials, dividends via AlphaVantage & yFinance.
- **Scraper Agent:** Retrieves SEC filings using Edgar/BeautifulSoup/sec-edgar-api.
- **Retriever Agent:** Pulls relevant knowledge base/context from FAISS vector store.
- **Language Agent:** Synthesizes market briefs using a hosted LLM (Groq Llama-3, etc.).
- **Voice Agent:** (Optional) Speech-to-text and text-to-speech for voice queries.
- **Celery/Redis:** Used for background tasks like periodic FAISS index updates.

---
### 🛠️ Technologies & Tools Used

* [![LangChain](https://img.shields.io/badge/LangChain-blue)](https://www.langchain.com/)
* [![LangGraph](https://img.shields.io/badge/LangGraph-darkblue)](https://github.com/langchain-ai/langgraph)
* [![Streamlit](https://img.shields.io/badge/Streamlit-red)](https://streamlit.io/)
* [![FastAPI](https://img.shields.io/badge/FastAPI-teal)](https://fastapi.tiangolo.com/)
* [![Python](https://img.shields.io/badge/Python-yellow)](https://www.python.org/)
* [![Pinecone](https://img.shields.io/badge/Pinecone-black)](https://www.pinecone.io/)
* [![Cohere](https://img.shields.io/badge/Cohere-purple)](https://cohere.com/)
* [![Groq](https://img.shields.io/badge/Groq-black)](https://groq.com/)
* [![yFinance](https://img.shields.io/badge/yFinance-orange)](https://pypi.org)*

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
```

2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Environment Variables

Create a .env in the root or in each agent’s folder as needed:


``` bash
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
``` bash
uvicorn agents.api_agent.main:app --host 0.0.0.0 --port 8001
uvicorn agents.api_agent.main:app --port 8001 
uvicorn agents.scraper_agent.main:app --port 8002 
uvicorn agents.retriever_agent.main:app --port 8003 
uvicorn agents.language_agent.main:app --port 8004 
uvicorn agents.voice_agent.main:app --port 8005 
uvicorn agents.orchestrator_agent.main:app --port 8006 
```
Streamlit Frontend:
``` bash
streamlit run stream_app/main.py
```


API Endpoints

(For full OpenAPI docs, run any FastAPI agent and visit /docs!)
``` bash
    API Agent: /quote — POST — market data, prices, info, historicals

    Scraper Agent: /filing — POST — fetch latest SEC filings for a CIK/type

    Retriever Agent: /retrieve — POST — fetch relevant text chunks from FAISS KB

    Language Agent: /analyze_graph — POST — generate answer from question/context
    /extract_symbols — POST — extract tickers from question

    Voice Agent: /voice_brief — POST (audio in, audio out); /tts — POST (text to mp3)

    Orchestrator Agent: /orchestrate — POST — main entry for frontend

```



 Deployment

Recommended: Render.com

Each agent gets its own Web Service on Render.

 
   

    Deploy Streamlit frontend last, pointing to your orchestrator’s public endpoint.

 


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

## Roadmap & Future Improvements

Add more test functions for all agents and end-to-end flows.

Switch voice pipeline to use cloud-based TTS for production.

Further optimize API latency and multi-agent orchestration.

Add more coverage for ETFs, global stocks, and CIK/ticker lookup tables.

Add monitoring/logging dashboards for easier debugging.

    Video Demo: Work in progress, will be shared soon.

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top"><strong>Back to top</strong></a>)</p>

 #

<div align="center">
    <h2 style="font-size: 36px; font-weight: bold; color: #4CAF50; text-transform: uppercase; letter-spacing: 3px;">
        Get in Touch
    </h2>
    <p style="font-size: 20px; font-style: italic; color: #333;">I’d love to hear from you!</p>
    <p style="font-size: 18px; color: #FF6347;">
        Nikhil Kumar Singh<br>
        <a href="https://www.linkedin.com/in/nikhil9981/" style="color: #4CAF50; text-decoration: none; font-weight: bold;">@nikhil9981</a><br>
        <a href="mailto:rathaurnikhil14@gmail.com" style="color: #4CAF50; text-decoration: none; font-weight: bold;">rathaurnikhil14@gmail.com</a><br><br>
        Project Link: 
        <a href="https://github.com/Nikhil-9981/AI_Agent_for_CSV_files" style="color: #FF6347; font-weight: bold; text-decoration: none;">AI Agent for CSV Files</a>
    </p>
    <h1 style="font-size: 60px; font-weight: bold; color: #FF6347; text-transform: uppercase; letter-spacing: 5px;">
        THANK YOU!
    </h1>
    <p style="font-size: 24px; font-style: italic; color: #555;">
        Your time and attention mean the world! ✨
    </p>
</div>
