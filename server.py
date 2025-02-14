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
CORS(app)  # Enable CORS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Load Vosk Model
model_path = "models/vosk-model-small-en-us-0.15"
model = vosk.Model(model_path)

# Audio setup
device_index = 2  # Change based on sd.query_devices()
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

def transcribe_audio():
    """
    Continuously reads audio from the microphone,
    runs Vosk recognition, and emits partial/final transcripts.
    """
    global printed_words, partial_text, is_transcribing, audio_stream
    recognizer = vosk.KaldiRecognizer(model, samplerate)
    printed_words = []  # Reset words when starting new session
    partial_text = ""

    def callback(indata, frames, time, status):
        if status:
            print(status)
        if is_transcribing:  # Only process audio when transcribing is active
            q.put(bytes(indata))

    # Start audio input stream
    with sd.RawInputStream(
        samplerate=samplerate,
        blocksize=blocksize,
        device=device_index,
        dtype="int16",
        channels=1,
        callback=callback
    ) as stream:
        audio_stream = stream
        print("Audio stream started.")

        while is_transcribing:
            try:
                data = q.get(timeout=0.5)  # Add timeout to allow checking is_transcribing
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())["text"]
                    if result:
                        new_words = result.split()
                        printed_words.extend(new_words)
                        final_text = " ".join(printed_words)
                        socketio.emit("transcription", {"text": final_text}, namespace="/")
                else:
                    partial_result = json.loads(recognizer.PartialResult())["partial"]
                    if partial_result and partial_result != partial_text:
                        socketio.emit("transcription",
                                    {"text": " ".join(printed_words) + " " + partial_result},
                                    namespace="/")
                        partial_text = partial_result
            except queue.Empty:
                continue  # No data available, continue checking is_transcribing

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
    port = int(os.environ.get("PORT", 10000))  # Use Render's PORT or default to 10000
    socketio.run(app, host="0.0.0.0", port=8080, debug=True)