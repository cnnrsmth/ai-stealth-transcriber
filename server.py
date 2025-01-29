from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
import queue
import json
import sounddevice as sd
import vosk
import threading

# Initialize Flask app & WebSockets
app = Flask(__name__)
CORS(app)  # Enable CORS
# Using "threading" here just as in your original code
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

@app.route("/")
def index():
    # Renders "index.html" from your "templates" folder
    return render_template("index.html")

def transcribe_audio():
    """
    Continuously reads audio from the microphone,
    runs Vosk recognition, and emits partial/final transcripts.
    """
    global printed_words, partial_text
    recognizer = vosk.KaldiRecognizer(model, samplerate)

    # Inner callback function for sounddevice
    def callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(bytes(indata))

    # Start audio input stream
    with sd.RawInputStream(
        samplerate=samplerate,
        blocksize=blocksize,
        device=device_index,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        print("Listening... Speak now (Web App will update automatically).")

        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())["text"]
                if result:
                    new_words = result.split()
                    printed_words.extend(new_words)
                    final_text = " ".join(printed_words)

                    # Emit final text to the client
                    socketio.emit("transcription", {"text": final_text}, namespace="/")
            else:
                # Partial (live) transcription
                partial_result = json.loads(recognizer.PartialResult())["partial"]
                if partial_result and partial_result != partial_text:
                    # Combine partial result with the final words so far
                    socketio.emit("transcription",
                                  {"text": " ".join(printed_words) + " " + partial_result},
                                  namespace="/")
                    partial_text = partial_result

# Start transcription in the background so Flask remains responsive
transcription_thread = threading.Thread(target=transcribe_audio, daemon=True)
transcription_thread.start()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080, debug=True)