# utils.py
# Utility functions for language detection, translation, and speech processing

from langdetect import detect
from gtts import gTTS
import tempfile
import os
import streamlit as st

try:
    import speech_recognition as sr
except ImportError:
    sr = None

# -------------------------------------------------------
# Language Detection
# -------------------------------------------------------
def detect_language(text: str) -> str:
    """Detect language from text and return ISO code (en, hi, pa)."""
    try:
        lang = detect(text)
        if lang.startswith("hi"):
            return "hi"
        elif lang.startswith("pa"):
            return "pa"
        else:
            return "en"
    except Exception:
        return "en"

# -------------------------------------------------------
# Translation
# -------------------------------------------------------
def translate_text(text: str, target_lang: str) -> str:
    """Dummy translation (for demo). Extend with deep_translator or IndicTrans if available."""
    if target_lang == "en":
        return text
    elif target_lang == "hi":
        return "अनुवाद: " + text
    elif target_lang == "pa":
        return "ਅਨੁਵਾਦ: " + text
    return text

# -------------------------------------------------------
# Text To Speech
# -------------------------------------------------------
def tts_play_bytes(text: str, lang: str = "en"):
    """Generate TTS audio bytes from text."""
    try:
        if lang not in ["en", "hi", "pa"]:
            lang = "en"
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tmp_path = fp.name
        tts.save(tmp_path)
        audio_bytes = open(tmp_path, "rb").read()
        os.remove(tmp_path)
        return audio_bytes
    except Exception as e:
        st.warning(f"TTS failed: {e}")
        return None

# -------------------------------------------------------
# Speech To Text (Audio Transcription)
# -------------------------------------------------------
def transcribe_audio_streamlit(audio_file):
    """Convert uploaded audio to text using SpeechRecognition."""
    if sr is None:
        st.warning("SpeechRecognition not installed.")
        return ""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="en-IN")
            return text
    except Exception as e:
        st.warning(f"Audio transcription failed: {e}")
        return ""
