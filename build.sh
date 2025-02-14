#!/bin/bash
set -e  # Exit on error

echo "Installing system dependencies..."
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
apt-get update && apt-get install -y \
    git-lfs \
    portaudio19-dev \
    libasound2-dev \
    libffi-dev \
    python3-dev \
    gcc \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    wget \
    unzip

echo "Installing Python packages..."
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "Downloading Vosk model..."
if [ ! -d "models/vosk-model-small-en-us-0.15" ]; then
    mkdir -p models
    wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    unzip vosk-model-small-en-us-0.15.zip -d models/
    rm vosk-model-small-en-us-0.15.zip
fi

echo "Build completed successfully!"