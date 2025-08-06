FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y espeak-ng && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the application code
COPY main.py /app/main.py

# Install Python dependencies
RUN pip install --no-cache-dir kokoro>=0.9.4 fastapi uvicorn

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]