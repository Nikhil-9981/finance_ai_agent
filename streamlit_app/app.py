import os
import tempfile
import requests
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings

# ——— Configuration ———
VOICE_AGENT_URL = os.getenv("VOICE_AGENT_URL", "http://localhost:8005/voice_brief")

# Optional webrtc config (you can tweak ICE servers, etc.)
WEBRTC_CLIENT_SETTINGS = ClientSettings(
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"audio": True, "video": False},
)

st.set_page_config("Voice-Enabled Finance AI", layout="centered")

st.title("🗣️ Finance AI Assistant — Voice Interface")

mode = st.radio("Select input mode:", ["Upload Audio File", "Record via Microphone"])

if mode == "Upload Audio File":
    audio_file = st.file_uploader("Upload a WAV/MP3 file", type=["wav", "mp3", "m4a"])
    if audio_file:
        if st.button("Send to Assistant"):
            with st.spinner("Generating market brief…"):
                # send to /voice_brief
                files = {"file": (audio_file.name, audio_file.read(), audio_file.type)}
                resp = requests.post(VOICE_AGENT_URL, files=files)
                if resp.status_code != 200:
                    st.error(f"Error {resp.status_code}: {resp.text}")
                else:
                    # display returned audio
                    st.success("Here’s your market brief:")
                    st.audio(resp.content, format="audio/mp3")
elif mode == "Record via Microphone":
    st.info("Click ▶️ to start recording. Click ▶️ again to stop and send.")
    webrtc_ctx = webrtc_streamer(
        key="voice-recorder",
        mode=WebRtcMode.SENDONLY,
        client_settings=WEBRTC_CLIENT_SETTINGS,
        sendback_audio=False,
    )

    if webrtc_ctx.audio_receiver:
        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
        if audio_frames:
            # Once we have at least one frame, enable the Send button
            if st.button("Send Recording to Assistant"):
                with st.spinner("Processing recording…"):
                    # write out to WAV
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp_path = tmp.name
                        tmp.write(b"".join([f.to_ndarray().tobytes() for f in audio_frames]))
                    # send file
                    with open(tmp_path, "rb") as f:
                        files = {"file": ("recording.wav", f, "audio/wav")}
                        resp = requests.post(VOICE_AGENT_URL, files=files)
                    os.unlink(tmp_path)
                    if resp.status_code != 200:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                    else:
                        st.success("Here’s your market brief:")
                        st.audio(resp.content, format="audio/mp3")

st.markdown("---")
st.markdown("Built with FastAPI voice agent • Streamlit • faster-whisper/Coqui or OpenAI TTS")
