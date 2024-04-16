import os
import wave
import pyaudio
import torch
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from faster_whisper import WhisperModel

device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(device)

app = Flask(__name__)
socketio = SocketIO(app)

model_size = "medium.en"
model = WhisperModel(model_size, device="cuda",
                     compute_type="float16", num_workers=2)

accumulated_transcription = ""
lock = threading.Lock()


def record_chunk(p, stream, file_path, chunk_length=1):
    frames = []
    for _ in range(0, int(16000 / 1024 * chunk_length)):
        data = stream.read(1024)
        frames.append(data)

    wf = wave.open(file_path, "wb")
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()


def transcribe_chunk(model, chunk_file):
    segments, _ = model.transcribe(chunk_file, beam_size=5)
    if segments:
        for segment in segments:
            return segment.text
    else:
        return ""


@socketio.on('audio')
def handle_audio():
    global accumulated_transcription
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1,
                    rate=16000, input=True, frames_per_buffer=1024)

    try:
        while True:
            chunk_file = "temp_chunk.wav"
            record_chunk(p, stream, chunk_file)
            transcription = transcribe_chunk(model, chunk_file)
            if transcription:
                with lock:
                    accumulated_transcription += transcription + " "
            emit('transcription', transcription)
            os.remove(chunk_file)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    socketio.run(app, host='localhost', port=5000)
