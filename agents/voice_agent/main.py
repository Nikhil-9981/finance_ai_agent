import os
import logging
import tempfile
import requests

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import speech_recognition as sr
import pyttsx3

# ---- Logging setup ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("voice_agent")

app = FastAPI(title="Voice Agent – Offline STT/TTS")

# Initialize TTS engine once
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)  # speaking rate

@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    """
    Offline speech-to-text via PocketSphinx.
    """
    logger.info(f"STT: Received audio file: {file.filename}")
    # Save to temp WAV
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        data = await file.read()
        tmp.write(data)
        wav_path = tmp.name

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_sphinx(audio)
        logger.info(f"STT: Transcribed text: {text!r}")
    except sr.UnknownValueError:
        logger.error("STT: Sphinx could not understand audio")
        text = ""
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(500, f"STT failed: {e}")
    finally:
        os.unlink(wav_path)

    return {"text": text}

@app.post("/tts")
async def tts_endpoint(text: str = Form(...)):
    """
    Offline text-to-speech via pyttsx3.
    """
    logger.info(f"TTS: Received text: {text[:100]!r}")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name

    try:
        # Synthesize and save to file
        tts_engine.save_to_file(text, out_path)
        tts_engine.runAndWait()
        logger.info(f"TTS: Audio saved at {out_path}")
    except Exception as e:
        logger.error(f"TTS error: {e}")
        os.unlink(out_path)
        raise HTTPException(500, f"TTS failed: {e}")

    return FileResponse(out_path, media_type="audio/mpeg", filename="tts_output.mp3")

@app.post("/voice_brief")
async def voice_brief(file: UploadFile = File(...)):
    """
    Full pipeline: audio → STT → query Language Agent → TTS → return audio.
    """
    # 1. STT
    stt_resp = await stt(file)
    question = stt_resp.get("text", "")
    if not question:
        raise HTTPException(400, "Could not transcribe audio")

    # 2. LLM query
    LANG_URL = os.getenv("LANGUAGE_AGENT_URL", "http://localhost:8004/analyze_graph")
    try:
        resp = requests.post(LANG_URL, json={"question": question}, timeout=30)
        resp.raise_for_status()
        answer = resp.json().get("answer", "")
        logger.info(f"Voice Brief: LLM answered: {answer!r}")
    except Exception as e:
        logger.error(f"Voice Brief LLM error: {e}")
        raise HTTPException(502, f"Language Agent failed: {e}")

    # 3. TTS
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name
    try:
        tts_engine.save_to_file(answer, out_path)
        tts_engine.runAndWait()
        logger.info(f"Voice Brief: TTS audio at {out_path}")
    except Exception as e:
        logger.error(f"Voice Brief TTS error: {e}")
        os.unlink(out_path)
        raise HTTPException(500, f"TTS failed: {e}")

    return FileResponse(out_path, media_type="audio/mpeg", filename="voice_brief.mp3")

@app.get("/ping")
def ping():
    return {"msg": "voice agent up"}
