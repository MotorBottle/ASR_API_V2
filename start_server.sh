#!/bin/bash

# ASR API Server V2 - Start Script

echo "Starting ASR API Server V2..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Source environment variables
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Set defaults
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-7869}
DEVICE=${DEVICE:-cpu}
LANGUAGE=${LANGUAGE:-zh}

echo "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Device: $DEVICE"
echo "  Language: $LANGUAGE"

# Start the server
python main.py