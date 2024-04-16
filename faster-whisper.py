import os
import wave
import pyaudio
import torch
import threading

from faster_whisper import WhisperModel

device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(device)


def record_chunk(p, stream, file_path, chunk_length=0.5):
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


def main():
    model_size = "large-v3"
    model = WhisperModel(model_size, device="cuda",
                         compute_type="float16", num_workers=2)

    print("Start...")

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1,
                    rate=16000, input=True, frames_per_buffer=1024)

    accumulated_transcription = ""
    lock = threading.Lock()

    def transcription_worker():
        nonlocal accumulated_transcription
        try:
            while True:
                chunk_file = "temp_chunk.wav"
                record_chunk(p, stream, chunk_file)
                transcription = transcribe_chunk(model, chunk_file)
                if transcription:
                    with lock:
                        accumulated_transcription += transcription + " "
                print(accumulated_transcription)
                os.remove(chunk_file)
        except KeyboardInterrupt:
            print("Stopping...")

    try:
        thread = threading.Thread(target=transcription_worker)
        thread.daemon = True
        thread.start()

        input("Press Enter to stop recording...")

    finally:
        with lock:
            print("Log: " + accumulated_transcription)
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main()
