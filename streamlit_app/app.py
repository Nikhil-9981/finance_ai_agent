import os
import tempfile
import requests
import wave
import numpy as np
import soundfile as sf  # For debugging the saved WAV file
import logging

import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

logger = logging.getLogger("streamlit_app")
logging.getLogger("streamlit_webrtc").setLevel(logging.ERROR)

# ——— Configuration ———
VOICE_AGENT_URL = os.getenv("VOICE_AGENT_URL", "https://finance-ai-agent-1-u7bk.onrender.com/tts")
ORCH_URL = os.getenv("ORCHESTRATOR_AGENT_URL", "https://finance-ai-agent-rfqw.onrender.com/orchestrate")
VOICE_TTS_URL = os.getenv("VOICE_TTS_URL", "https://finance-ai-agent-1-u7bk.onrender.com/voice_brief")

WEBRTC_RTC_CONFIGURATION = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})
MEDIA_CONSTRAINTS = {"audio": True, "video": False}

st.set_page_config(page_title="Voice-Enabled Finance AI", layout="centered")
st.title("🗣️ Finance AI Assistant — Voice Interface")

def save_audio_frames_to_mono_wav(audio_frames, wav_path, sample_rate):
    # Converts any input to mono 16-bit PCM, contiguous
    with wave.open(wav_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        for frame in audio_frames:
            arr = frame.to_ndarray()
            if arr.ndim > 1:
                arr = np.mean(arr, axis=1)
            if arr.dtype != np.int16:
                arr = (arr * 32767).clip(-32768, 32767).astype(np.int16)
            arr = np.ascontiguousarray(arr)
            wf.writeframes(arr.tobytes())
    # Log and debug the output file
    try:
        data, sr = sf.read(wav_path)
        logger.info(f"[DEBUG] Saved WAV: shape={data.shape}, sr={sr}, dtype={data.dtype}")
    except Exception as e:
        logger.error(f"[DEBUG] Could not read saved WAV for inspection: {e}")

mode = st.radio("Select input mode:", [
    "Upload Audio File",
    "Type Text (verbal answer)"
])

if mode == "Upload Audio File":
    audio_file = st.file_uploader("Upload a WAV/MP3 file", type=["wav", "mp3", "m4a"])
    if audio_file and st.button("Send to Assistant"):
        with st.spinner("Generating market brief…"):
            logger.info(f"User uploaded file: {audio_file.name} ({audio_file.type})")
            file_suffix = os.path.splitext(audio_file.name)[-1]
            with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp:
                tmp.write(audio_file.read())
                upload_path = tmp.name
            logger.info(f"Saved upload to {upload_path}")

            try:
                with open(upload_path, "rb") as f:
                    files = {"file": (audio_file.name, f, audio_file.type)}
                    logger.info(f"Sending audio file to voice agent: {VOICE_AGENT_URL}")
                    resp = requests.post(VOICE_AGENT_URL, files=files)
                os.unlink(upload_path)
            except Exception as e:
                logger.error(f"Error sending file to voice agent: {e}")
                st.error(f"Error sending file: {e}")
                resp = None

            if resp is not None:
                if resp.status_code != 200:
                    logger.error(f"Voice agent error {resp.status_code}: {resp.text}")
                    st.error(f"Error {resp.status_code}: {resp.text}")
                else:
                    logger.info("Received successful response from voice agent.")
                    st.success("Here’s your market brief:")
                    st.audio(resp.content, format="audio/mp3")

 

elif mode == "Type Text (verbal answer)":
    user_text = st.text_area("Type your finance question here:")
    if st.button("Send to Assistant") and user_text.strip():
        with st.spinner("Generating answer…"):
            try:
                # Step 1: Ask orchestrator for text answer
                resp = requests.post(ORCH_URL, json={"question": user_text}, timeout=300)
                resp.raise_for_status()
                answer = resp.json().get("answer", "")
                st.success("Here’s your market brief:")
                st.write(answer)

                # Step 2: TTS audio
                tts_resp = requests.post(
                    VOICE_TTS_URL, data={"text": answer}
                )
                if tts_resp.status_code == 200:
                    st.audio(tts_resp.content, format="audio/mp3")
                else:
                    st.warning("Could not generate audio.")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")
st.markdown("Built with FastAPI voice agent • Streamlit • streamlit-webrtc")
