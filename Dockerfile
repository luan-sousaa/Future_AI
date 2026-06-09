# Shared image for both the ADK API server and the Streamlit front-end.
# The same image is launched with different commands in docker-compose.yml.
FROM python:3.11-slim

# Keep Python output unbuffered and skip .pyc files in the container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies first so the layer is cached across code changes.
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application code.
COPY . .

# 8000 -> ADK API server, 8501 -> Streamlit. Documentation only; the actual
# published ports are defined in docker-compose.yml.
EXPOSE 8000 8501

# Default command runs the agent API. docker-compose overrides this for the
# Streamlit service.
CMD ["adk", "api_server", ".", "--host", "0.0.0.0", "--port", "8000"]
