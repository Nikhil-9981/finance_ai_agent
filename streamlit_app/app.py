# streamlit_app/app.py

import os
import tempfile
import requests
import wave
import numpy as np

import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

# ——— Configuration ———
VOICE_AGENT_URL = os.getenv("VOICE_AGENT_URL", "http://localhost:8005/voice_brief")

# WebRTC settings
WEBRTC_RTC_CONFIGURATION = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})
MEDIA_CONSTRAINTS = {"audio": True, "video": False}

st.set_page_config(page_title="Voice-Enabled Finance AI", layout="centered")
st.title("🗣️ Finance AI Assistant — Voice Interface")

def save_audio_frames_to_mono_wav(audio_frames, wav_path, sample_rate):
    """Convert any multi-channel input to mono and save as a proper WAV file."""
    with wave.open(wav_path, 'wb') as wf:
        wf.setnchannels(1)  # Mono always!
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        for frame in audio_frames:
            arr = frame.to_ndarray()
            if arr.ndim > 1:
                arr = arr.mean(axis=1)  # Downmix to mono
            if arr.dtype != np.int16:
                arr = (arr * np.iinfo(np.int16).max).astype(np.int16)
            wf.writeframes(arr.tobytes())

mode = st.radio("Select input mode:", ["Upload Audio File", "Record via Microphone"])

if mode == "Upload Audio File":
    audio_file = st.file_uploader("Upload a WAV/MP3 file", type=["wav", "mp3", "m4a"])
    if audio_file and st.button("Send to Assistant"):
        with st.spinner("Generating market brief…"):
            # If needed, save to temp file for WAV enforcement (e.g., non-WAV uploads)
            file_suffix = os.path.splitext(audio_file.name)[-1]
            with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp:
                tmp.write(audio_file.read())
                upload_path = tmp.name

            # Optionally: Convert to mono WAV here if you want 100% certainty backend will always work
            # For .wav, can re-save as mono. For mp3/m4a, backend should handle conversion or you need ffmpeg.
            # We'll just send the file as-is for now.
            with open(upload_path, "rb") as f:
                files = {"file": (audio_file.name, f, audio_file.type)}
                resp = requests.post(VOICE_AGENT_URL, files=files)
            os.unlink(upload_path)

            if resp.status_code != 200:
                st.error(f"Error {resp.status_code}: {resp.text}")
            else:
                st.success("Here’s your market brief:")
                st.audio(resp.content, format="audio/mp3")

elif mode == "Record via Microphone":
    st.info("Click ▶️ to start recording. Click ▶️ again to stop and send.")
    webrtc_ctx = webrtc_streamer(
        key="voice-recorder",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=WEBRTC_RTC_CONFIGURATION,
        media_stream_constraints=MEDIA_CONSTRAINTS,
    )

    if webrtc_ctx.audio_receiver:
        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
        if audio_frames and st.button("Send Recording to Assistant"):
            with st.spinner("Processing recording…"):
                # Always save as mono WAV!
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    wav_path = tmp.name
                sample_rate = audio_frames[0].sample_rate if audio_frames else 48000
                save_audio_frames_to_mono_wav(audio_frames, wav_path, sample_rate)

                # Send to voice agent
                with open(wav_path, "rb") as f:
                    files = {"file": ("recording.wav", f, "audio/wav")}
                    resp = requests.post(VOICE_AGENT_URL, files=files)
                os.unlink(wav_path)

                if resp.status_code != 200:
                    st.error(f"Error {resp.status_code}: {resp.text}")
                else:
                    st.success("Here’s your market brief:")
                    st.audio(resp.content, format="audio/mp3")

st.markdown("---")
st.markdown("Built with FastAPI voice agent • Streamlit • streamlit-webrtc")
