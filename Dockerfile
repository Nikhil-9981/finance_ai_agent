# ============================
# Stage 1: Builder
# ============================
FROM python:3.11-slim AS builder

# Fix casing warning (FROM and AS match case)
# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY retriever_agent_requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r retriever_agent_requirements.txt

# ============================
# Stage 2: Final minimal image
# ============================
FROM python:3.11-slim AS final

# Install runtime-only dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY ./agents/retriever_agent ./agents/retriever_agent
COPY ./data_ingestion ./data_ingestion

EXPOSE 8003

CMD ["uvicorn", "agents.retriever_agent.main:app", "--host", "0.0.0.0", "--port", "8003"]
