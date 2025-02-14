from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import queue
import json
import sounddevice as sd
import vosk
import threading
import os
import time

# Initialize Flask app & WebSockets
app = Flask(__name__)
CORS(app)  # Allow all origins in development
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Load Vosk Model
model_path = "models/vosk-model-small-en-us-0.15"
if not os.path.exists(model_path):
    raise RuntimeError(f"Please download the model from https://alphacephei.com/vosk/models and unpack as {model_path}")

model = vosk.Model(model_path)

# Audio setup
try:
    device_info = sd.query_devices(None, 'input')
    device_index = device_info['index']  # Use default input device
    samplerate = int(device_info['default_samplerate'])
except Exception as e:
    print(f"Error setting up audio device: {e}")
    device_index = None  # Will use system default
    samplerate = 16000

blocksize = 4000
q = queue.Queue()
printed_words = []
partial_text = ""

# Control flags
is_transcribing = False
audio_stream = None
transcription_thread = None

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on('audio_data')
def handle_audio_data(data):
    if not is_transcribing:
        return
        
    try:
        # Convert the received data to bytes
        audio_data = bytes(data)
        print(f"Received audio data length: {len(audio_data)} bytes")  # Debug log
        q.put(audio_data)
    except Exception as e:
        print(f"Error processing audio data: {e}")
        print(f"Data type received: {type(data)}")  # Debug log
        print(f"Data length: {len(data) if hasattr(data, '__len__') else 'unknown'}")  # Debug log

def transcribe_audio():
    """
    Process audio data from the client and run Vosk recognition
    """
    global printed_words, partial_text, is_transcribing
    recognizer = vosk.KaldiRecognizer(model, 16000)  # Fixed sample rate to match client
    printed_words = []  # Reset words when starting new session
    partial_text = ""
    processed_chunks = 0  # Debug counter

    while is_transcribing:
        try:
            data = q.get(timeout=0.5)
            processed_chunks += 1  # Increment counter
            if processed_chunks % 10 == 0:  # Log every 10th chunk
                print(f"Processed {processed_chunks} audio chunks")
            
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())["text"]
                if result:
                    print(f"Recognition result: {result}")  # Debug log
                    new_words = result.split()
                    printed_words.extend(new_words)
                    final_text = " ".join(printed_words)
                    socketio.emit("transcription", {"text": final_text})
            else:
                partial_result = json.loads(recognizer.PartialResult())["partial"]
                if partial_result and partial_result != partial_text:
                    print(f"Partial result: {partial_result}")  # Debug log
                    socketio.emit("transcription",
                                {"text": " ".join(printed_words) + " " + partial_result})
                    partial_text = partial_result
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error in transcription: {e}")
            print(f"Error details: {str(e)}")
            print(f"Data length that caused error: {len(data) if 'data' in locals() else 'unknown'}")  # Debug log
            continue

    print("Transcription stopped.")

@socketio.on("start_transcription")
def handle_start_transcription():
    global is_transcribing, transcription_thread
    if not is_transcribing:
        is_transcribing = True
        transcription_thread = threading.Thread(target=transcribe_audio, daemon=True)
        transcription_thread.start()
        print("Transcription started")

@socketio.on("stop_transcription")
def handle_stop_transcription():
    global is_transcribing, audio_stream, transcription_thread
    if is_transcribing:
        is_transcribing = False
        # Clear the queue
        while not q.empty():
            q.get()
        print("Transcription stopped")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    debug = os.environ.get("FLASK_ENV") == "development"
    host = "0.0.0.0"
    
    print(f"Starting server on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Audio device index: {device_index}")
    print(f"Sample rate: {samplerate}")
    
    socketio.run(app, host=host, port=port, debug=debug)