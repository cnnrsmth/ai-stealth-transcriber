#!/usr/bin/env bash
set -eux

# Install PortAudio (required for PyAudio and Sounddevice)
apt-get update && apt-get install -y portaudio19-dev