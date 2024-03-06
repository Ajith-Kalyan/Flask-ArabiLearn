import os
import wave
from faster_whisper import WhisperModel
import pyaudio
import torch

from transformers import pipeline
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(device)

#pipe_arabic = pipeline("automatic-speech-recognition", model="faster/whisper-large-v3", generate_kwargs={"language":"english"}, device=device)
# import os
# os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
def record_chunk(p, stream, file_path, chunk_length=5):
    frames = []
    for _ in range(0, int(16000/ 1024 * chunk_length)):
        data = stream.read(1024)
        frames.append(data)

    wf = wave.open(file_path, "wb")
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()

def transcribe_chunk(model, chunk_file):
    # return pipe_arabic(chunk_file)['text']
    segments, info = model.transcribe(chunk_file, beam_size=5)
    for segment in segments:
        return segment.text

def main2():
    model_size = "large-v2.ar"

    # Run on GPU with FP16
    # model = WhisperModel(model_size, device="cuda", compute_type="float16")

    # or run on GPU with INT8
    model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
    # or run on CPU with INT8
    # model = WhisperModel(model_size, device="cpu", compute_type="int8")
    print("Start...")
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

    accumulated_transcription = ""

    try:
        while True:
            chunk_file = "temp_chunk.wav"
            record_chunk(p, stream, chunk_file)
            transcription = transcribe_chunk(model, chunk_file)
            print(transcription)
            os.remove(chunk_file)

            accumulated_transcription += transcription + " "
    except KeyboardInterrupt:
        print("Stopping..")
        with open("log.txt", "w") as log_file:
            log_file.write(accumulated_transcription)
    finally:
        print("Log: "+accumulated_transcription)
        stream.stop_stream()
        stream.close()
        p.terminate()
        
if __name__ == "__main__":
    main2()
# segments, info = model.transcribe("./uploads/1.wav", beam_size=5)

# print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

# for segment in segments:
#     print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))