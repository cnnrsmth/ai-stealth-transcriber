#!/usr/bin/env bash
set -eux  # Exit on error, print each command

# Install system dependencies, including PortAudio
apt-get update && apt-get install -y portaudio19-dev

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt