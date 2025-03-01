import os
import PyPDF2
import pyttsx3
from gtts import gTTS
from flask import Flask, render_template, request, send_from_directory, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text.strip()

# Convert text to speech (Offline - pyttsx3)
def text_to_speech_offline(text, output_file, voice_id=0, rate=150, volume=1.0):
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    if voice_id < len(voices):
        engine.setProperty("voice", voices[voice_id].id)
    else:
        engine.setProperty("voice", voices[0].id)
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)
    engine.save_to_file(text, output_file)
    engine.runAndWait()

# Convert text to speech (Online - gTTS)
def text_to_speech_online(text, output_file, lang="en"):
    tts = gTTS(text=text, lang=lang)
    tts.save(output_file)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/online")
def online():
    return render_template("online.html")

@app.route("/convert", methods=["POST"])
def convert():
    mode = request.form["mode"]
    
    if mode == "online":
        return redirect(url_for("online"))

    audio_url = None
    text = request.form.get("text", "").strip()
    voice_id = int(request.form.get("voice_id", 0))

    if not text and "pdf" in request.files:
        file = request.files["pdf"]
        if file:
            filename = secure_filename(file.filename)
            pdf_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(pdf_path)
            text = extract_text_from_pdf(pdf_path)
    
    if text:
        output_file = os.path.join(OUTPUT_FOLDER, "audiobook.mp3")
        text_to_speech_offline(text, output_file, voice_id)
        audio_url = f"/output/audiobook.mp3"

    return jsonify({"audio_url": audio_url, "last_text": text})

@app.route("/convert_online", methods=["POST"])
def convert_online():
    text = request.form.get("text", "").strip()
    lang = request.form.get("lang", "en")

    if text:
        output_file = os.path.join(OUTPUT_FOLDER, "audiobook.mp3")
        text_to_speech_online(text, output_file, lang)
        audio_url = f"/output/audiobook.mp3"
        return jsonify({"audio_url": audio_url, "last_text": text})

    return jsonify({"error": "No text provided"})

@app.route("/output/<path:filename>")
def serve_audio(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
