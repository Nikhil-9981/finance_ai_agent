# Use the official Python slim image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies (for building some Python packages)
RUN apt-get update && \
    apt-get install -y gcc build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY retriever_agent_requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r retriever_agent_requirements.txt

# Copy the actual application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start the FastAPI app (update path as needed)
CMD ["uvicorn", "agents.retriever_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
