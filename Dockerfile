# Use a lightweight python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install pip and the requirements
# Using --no-cache-dir keeps the image size small.
# Note: Since pt_core_news_sm is a direct wheel URL in requirements.txt,
# it gets downloaded and installed automatically without needing a separate spacy download command!
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the API port
EXPOSE $PORT

# Run the FastAPI server
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]
