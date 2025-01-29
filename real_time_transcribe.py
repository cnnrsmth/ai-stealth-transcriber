import queue
import sys
import sounddevice as sd
import vosk
import json

# Load Vosk Model
model_path = "models/vosk-model-small-en-us-0.15"  # Make sure the model path is correct
model = vosk.Model(model_path)

# Set up microphone input
device_index = 2  # Check with `python -c "import sounddevice as sd; print(sd.query_devices())"`
samplerate = 16000
blocksize = 4000  # Smaller blocksize = lower latency

q = queue.Queue()
printed_words = []  # Track words that have already been displayed
partial_text = ""  # Store last partial result

# Audio callback function
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))  # Convert audio to bytes and store in queue

# Function to extract only new words
def get_new_words(new_text, old_words):
    """Compares new_text with old_words list and returns only new words."""
    new_words = new_text.split()
    start_index = 0

    # Find where new words start
    for i in range(min(len(old_words), len(new_words))):
        if old_words[i] != new_words[i]:
            start_index = i
            break
    return " ".join(new_words[start_index:])  # Return only new portion

# Start transcription
with sd.RawInputStream(samplerate=samplerate, blocksize=blocksize, device=device_index, dtype="int16",
                        channels=1, callback=callback):
    print("Listening... Speak now (Press Ctrl+C to stop).\n")

    recognizer = vosk.KaldiRecognizer(model, samplerate)

    try:
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                # Extract final recognized words and prevent duplication
                result = json.loads(recognizer.Result())["text"]
                new_text = get_new_words(result, printed_words)  # Get only new words
                
                if new_text:  # Append only if there's new content
                    printed_words += new_text.split()  # Update stored words
                    print(new_text, end=" ", flush=True)  # Print new words smoothly
            else:
                # Print live (partial) results
                partial_result = json.loads(recognizer.PartialResult())["partial"]
                if partial_result and partial_result != partial_text:
                    print("\r" + " ".join(printed_words) + " " + partial_result + " ", end="", flush=True)
                    partial_text = partial_result  # Store last seen partial result

    except KeyboardInterrupt:
        print("\nTranscription stopped.")