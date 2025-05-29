# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY retriever_agent_requirements.txt .

# Install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r retriever_agent_requirements.txt

# Copy application code
COPY . .

# Make sure the FAISS index and .meta are available
# (Assumes they are present at /app/data_ingestion/faiss_index and faiss_index.meta)
# If they're outside repo, use a Docker COPY statement for those files specifically.

# Expose the correct port
EXPOSE 8003

# Command to run the FastAPI app
CMD ["uvicorn", "agents.retriever_agent.main:app", "--host", "0.0.0.0", "--port", "8003"]
