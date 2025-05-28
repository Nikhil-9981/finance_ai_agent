#!/bin/bash
uvicorn agents.api_agent.main:app --port 8001 & 
uvicorn agents.scraper_agent.main:app --port 8002 &
uvicorn agents.retriever_agent.main:app --port 8003 &
uvicorn agents.language_agent.main:app --port 8004 &
uvicorn agents.voice_agent.main:app --port 8005 &
uvicorn agents.orchestrator_agent.main:app --port 8006 &
wait
 