import requests
import os

BASE_URL = "http://localhost:8005"

def test_stt():
    """Test the /stt endpoint with a sample WAV file."""
    audio_path = "/home/nikhil-singh/Downloads/harvard.wav"
    assert os.path.exists(audio_path), f"Missing fixture: {audio_path}"
    with open(audio_path, "rb") as f:
        files = {"file": ("sample_question.wav", f, "audio/wav")}
        resp = requests.post(f"{BASE_URL}/stt", files=files, timeout=30)
    assert resp.status_code == 200, f"STT failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "text" in data, "No 'text' in STT response"
    assert isinstance(data["text"], str)
    # Empty transcript is allowed but still a valid response

def test_tts():
    """Test the /tts endpoint returns an audio content-type."""
    payload = {"text": "Hello world, this is a test."}
    resp = requests.post(f"{BASE_URL}/tts", data=payload, timeout=30)
    assert resp.status_code == 200, f"TTS failed: {resp.status_code} {resp.text}"
    content_type = resp.headers.get("content-type", "")
    assert content_type.startswith("audio/"), f"Unexpected Content-Type: {content_type}"

def test_voice_brief():
    """Test the end-to-end /voice_brief pipeline returns an audio content-type."""
    audio_path = "/home/nikhil-singh/Downloads/harvard.wav"
    assert os.path.exists(audio_path), f"Missing fixture: {audio_path}"
    with open(audio_path, "rb") as f:
        files = {"file": ("sample_question.wav", f, "audio/wav")}
        resp = requests.post(f"{BASE_URL}/voice_brief", files=files, timeout=90)
    assert resp.status_code == 200, f"voice_brief failed: {resp.status_code} {resp.text}"
    content_type = resp.headers.get("content-type", "")
    assert content_type.startswith("audio/"), f"Unexpected Content-Type: {content_type}"

if __name__ == "__main__":
    test_stt()
    test_tts()
    test_voice_brief()
