#!/usr/bin/env bash
set -eux  # Exit on error, print each command

# Ensure package lists are updated
apt-get update

# Install system dependencies needed for sounddevice
apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    libffi-dev \
    python3-dev \
    gcc \
    libportaudio2 \
    libportaudiocpp0

# Force reinstallation of sounddevice after installing system dependencies
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir --force-reinstall sounddevice
pip install --no-cache-dir -r requirements.txt