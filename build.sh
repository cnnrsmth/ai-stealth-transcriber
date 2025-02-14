#!/usr/bin/env bash
set -eux  # Exit on error, print commands

# Update package lists and install required system libraries
apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    libffi-dev \
    python3-dev \
    gcc

# Upgrade pip and install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt