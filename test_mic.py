import sounddevice as sd
import numpy as np

# Set the parameters for your microphone
samplerate = 16000
duration = 5  # seconds

# Record some data from the microphone
print("Testing microphone access...")
audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
sd.wait()  # Wait until the recording is finished

# Check if we have data
print("Recording finished. Data received:")
print(np.mean(audio_data))  # Output the mean to verify data was recorded