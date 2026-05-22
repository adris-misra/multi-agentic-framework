FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY config/ ./config/

# Install package
RUN pip install --no-cache-dir -e .

EXPOSE 8501

CMD ["streamlit", "run", "src/industrial_agents/ui/operator_copilot/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
