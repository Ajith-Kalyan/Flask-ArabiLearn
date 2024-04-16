# # pip install SpeechRecognition PyAudio

# # Make sure to update the device_index on line 34, to reflect the stero mixer on your computer
import concurrent.futures
import speech_recognition as sr
import time

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s: %(levelname)s - %(message)s"
)


def listen(mic, id):
    logging.debug(f"Listening... {id}")
    with mic as source:
        audio = r.listen(source, timeout=5, phrase_time_limit=3)
        return audio


def transcribe(audio):
    logging.debug(f"transcribing...")
    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return "..."  # Return a placeholder for unknown values


if __name__ == "__main__":
    r = sr.Recognizer()
    r.pause_threshold = 2

    mic = sr.Microphone(device_index=21)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            listener = executor.submit(listen, mic, 1)
            audio = listener.result()  # Wait for audio to be recorded
            subtitles = executor.submit(transcribe, audio)
            logging.info(subtitles.result())

# import pyaudioc

# # Create an instance of PyAudio
# p = pyaudio.PyAudio()

# # Get the number of audio I/O devices
# devices = p.get_device_count()

# # Iterate through all devices
# for i in range(devices):
#     # Get the device info
#     device_info = p.get_device_info_by_index(i)
#     # Check if this device is a microphone (an input device)
#     if device_info.get('maxInputChannels') > 0:
#         print(
#             f"Microphone: {device_info.get('name')} , Device Index: {device_info.get('index')}")
