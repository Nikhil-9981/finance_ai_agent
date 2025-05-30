import os
import logging
import tempfile
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import speech_recognition as sr
import pyttsx3
from gtts import gTTS

# Setup logging with timestamps and levels
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("voice_agent")

app = FastAPI(title="Voice Agent – Offline STT/TTS")

# Add CORS middleware (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domains in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global recognizer and pyttsx3 TTS engine instances
recognizer = sr.Recognizer()
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)

# Executor for running blocking code without blocking the event loop
executor = ThreadPoolExecutor()

@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    logger.info(f"STT: Received audio file: {file.filename}")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        data = await file.read()
        tmp.write(data)
        wav_path = tmp.name

    loop = asyncio.get_event_loop()

    def recognize_audio():
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_sphinx(audio)

    try:
        text = await loop.run_in_executor(executor, recognize_audio)
        logger.info(f"STT: Transcribed text: {text!r}")
    except sr.UnknownValueError:
        logger.error("STT: Sphinx could not understand audio")
        text = ""
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(500, f"STT failed: {e}")
    finally:
        try:
            os.unlink(wav_path)
        except Exception:
            pass

    return {"text": text}


@app.post("/tts")
async def tts_endpoint(text: str = Form(..., min_length=1, max_length=500), background_tasks: BackgroundTasks = None):
    logger.info(f"TTS: Received text: {text[:100]!r}")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name
    try:
        tts = gTTS(text, lang='en', slow=False)
        tts.save(out_path)
        logger.info(f"TTS: Audio saved at {out_path}")
    except Exception as e:
        logger.error(f"TTS error: {e}")
        try:
            os.unlink(out_path)
        except Exception:
            pass
        raise HTTPException(500, f"TTS failed: {e}")

    # Schedule temp file deletion after response
    if background_tasks:
        background_tasks.add_task(os.unlink, out_path)

    return FileResponse(out_path, media_type="audio/mpeg", filename="tts_output.mp3")


@app.post("/voice_brief")
async def voice_brief(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Full pipeline: audio → STT → Orchestrator → TTS → return audio.
    """
    stt_resp = await stt(file)
    question = stt_resp.get("text", "")
    if not question:
        raise HTTPException(400, "Could not transcribe audio")

    ORCH_URL = os.getenv("ORCHESTRATOR_AGENT_URL", "http://localhost:8006/orchestrate")
    try:
        resp = requests.post(ORCH_URL, json={"question": question}, timeout=60)
        resp.raise_for_status()
        answer = resp.json().get("answer", "")
        logger.info(f"Voice Brief: Orchestrator answered: {answer!r}")
    except Exception as e:
        logger.error(f"Voice Brief Orchestrator error: {e}")
        raise HTTPException(502, f"Orchestrator Agent failed: {e}")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name

    def save_tts():
        tts_engine.save_to_file(answer, out_path)
        tts_engine.runAndWait()

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(executor, save_tts)
        logger.info(f"Voice Brief: TTS audio at {out_path}")
    except Exception as e:
        logger.error(f"Voice Brief TTS error: {e}")
        try:
            os.unlink(out_path)
        except Exception:
            pass
        raise HTTPException(500, f"TTS failed: {e}")

    if background_tasks:
        background_tasks.add_task(os.unlink, out_path)

    return FileResponse(out_path, media_type="audio/mpeg", filename="voice_brief.mp3")


@app.get("/ping")
def ping():
    return {"msg": "voice agent up"}
