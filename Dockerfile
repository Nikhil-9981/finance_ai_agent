# Use the official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (add any you need)
RUN apt-get update && \
    apt-get install -y gcc build-essential ffmpeg && \
    apt-get clean

# Copy requirements and install
COPY api_agent_requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r api_agent_requirements.txt

# Copy your source code
COPY . .

# Expose the port (change if needed)
EXPOSE 8000

# Start FastAPI app (change this path to your agent!)
CMD ["uvicorn", "agents.api_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
