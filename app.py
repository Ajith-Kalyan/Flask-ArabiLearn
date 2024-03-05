import sqlite3
from flask import request
from flask import Flask, jsonify
from flask_cors import CORS
from audioConversion import convert_webm_to_wav
from draft import compare_words
from routes import audio_routes
from transformers import pipeline

app = Flask(__name__)
CORS(app)


#pipe_arabic = pipeline("automatic-speech-recognition", model="othrif/wav2vec2-large-xlsr-arabic")
pipe_arabic = pipeline("automatic-speech-recognition", model="openai/whisper-small", generate_kwargs={"language":"arabic"})


default_key = 0;
# app.register_blueprint(audio_routes)
def compare_words(actual, response_text):
    print("comparing")
    actual_words = actual.split()
    print("actual", actual_words)
    response_words = response_text.split()
    print("response", response_words)

    result = []

    # Concatenate actual and response text
    actual_concatenated = ' '.join(actual_words)
    response_concatenated = ' '.join(response_words)

    # Determine the maximum length between actual and response
    max_length = max(len(actual_words), len(response_words))

    for i in range(max_length):
        actual_word = actual_words[i] if i < len(actual_words) else ""
        response_word = response_words[i] if i < len(response_words) else ""

        if actual_word.lower() == response_word.lower():
            result.append({"Word": actual, "Response": response_text, "Status": "Correct"})
        else:
            result.append({"Word": actual, "Response": response_text, "Status": "Incorrect"})
            break  # Exit the loop if a mismatch is found

    return result



import asyncio
@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"})

    if file:
        audio_recording = './uploads/test/' + file.filename
        try:
            print(file.filename)
            file.save(audio_recording)
            wav_input = audio_recording
        
            # Connect to the SQLite database
            conn = sqlite3.connect('Translations.db')
            cursor = conn.cursor()

            # Retrieve the key parameter from the form data
            key = int(request.form['id'])

            # Retrieve the actual Arabic sentence based on the key parameter
            print(key)
            cursor.execute("SELECT arabicSentences FROM arabic_lessons WHERE id = ?", (key,))
            actual_arabic = cursor.fetchone()[0]

            # Transcribe the audio input asynchronously
            def transcribe_audio():
                print("transcribing")
                return pipe_arabic(wav_input)['text']

            # Perform word comparison asynchronously
            def perform_comparison():
                response_text = transcribe_audio()
                print(response_text)
                return compare_words(actual_arabic, response_text)

            # Execute the asynchronous tasks and wait for the comparison result
            comparison_result = perform_comparison();

            # Close the database connection
            conn.close()

            print(comparison_result)
            return jsonify({"actual": actual_arabic, "response_text": comparison_result[0]})

        except (IndexError, KeyError, OSError) as e:
            return jsonify({"error": f"Error processing audio file: {str(e)}"})
        except Exception as e:
            return jsonify({"error": f"Unexpected error: {str(e)}"})

@app.route('/GetWord/<int:id>', methods=['GET'])  # Receive the ID as a parameter
def getSentence(id):
    wordId = id

    # Connect to the SQLite database
    conn = sqlite3.connect('Translations.db')
    cursor = conn.cursor()

    # Retrieve the next sentence from the database
    cursor.execute("SELECT id, englishSentences, arabicSentences FROM arabic_lessons WHERE id = ?", (wordId,))
    row = cursor.fetchone()

    # Close the database connection
    conn.close()

    if row:
        print(row)
        id, english_sentence, arabic_sentence = row
        return jsonify({
            "id": id,
            "englishSentence": english_sentence,
            "arabicSentence": arabic_sentence
        })
    else:
        return jsonify({"error": "No more sentences available"})


# @app.route('/GetNext', methods=['GET'])
# def get_next_sentence():
#     global default_key

#     # Connect to the SQLite database
#     conn = sqlite3.connect('Translations.db')
#     cursor = conn.cursor()

#     # Retrieve the next sentence from the database
#     cursor.execute("SELECT id, englishSentences, arabicSentences FROM arabic_lessons WHERE id = ?", (default_key,))
#     row = cursor.fetchone()

#     # Increment default key for the next call
#     default_key += 1

#     # Close the database connection
#     conn.close()

#     if row:
#         print(row)
#         id, english_sentence, arabic_sentence = row
#         return jsonify({
#             "id": id,
#             "englishSentence": english_sentence,
#             "arabicSentence": arabic_sentence
#         })
#     else:
#         return jsonify({"error": "No more sentences available"})

# @app.route('/GetPrevious', methods=['GET'])
# def get_previous_sentence():
#     global default_key

#     # Decrement default key for the previous call
#     default_key = default_key - 1

#     # Connect to the SQLite database
#     conn = sqlite3.connect('Translations.db')
#     cursor = conn.cursor()

#     # Retrieve the previous sentence from the database
#     cursor.execute("SELECT id, englishSentences, arabicSentences FROM arabic_lessons WHERE id = ?", (default_key,))
#     row = cursor.fetchone()

#     # Close the database connection
#     conn.close()

#     if row:
#         id, english_sentence, arabic_sentence = row
#         return jsonify({
#             "id": id,
#             "englishSentence": english_sentence,
#             "arabicSentence": arabic_sentence
#         })
#     else:
#         return jsonify({"error": "No previous sentences available"})


if __name__ == '__main__':
    app.run(debug=True)
