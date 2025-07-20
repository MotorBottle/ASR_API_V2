# ASR API Server V2 - CPU/GPU Docker Image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for temporary files and ModelScope cache
RUN mkdir -p /tmp/asr_api /root/.cache/modelscope

# Set environment variables
ENV PYTHONPATH=/app
ENV DEVICE=cpu
ENV LANGUAGE=zh
ENV HOST=0.0.0.0
ENV PORT=7869

# Expose port
EXPOSE 7869

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7869/health || exit 1

# Run the application
CMD ["python", "main.py"]