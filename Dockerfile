FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Only system deps required for pip and numpy
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY retriever_agent_requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r retriever_agent_requirements.txt && \
    apt-get purge -y --auto-remove gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./agents/retriever_agent ./agents/retriever_agent
COPY ./data_ingestion ./data_ingestion

EXPOSE 8003

CMD ["uvicorn", "agents.retriever_agent.main:app", "--host", "0.0.0.0", "--port", "8003"]
