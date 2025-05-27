import requests
import time

def test_language_agent_analyze():
    """
    Test the /analyze endpoint of the Language Agent (Groq Llama 3.1/3.3 70B version).
    """
    url = "http://localhost:8004/analyze"
    payload = {
        "question": "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
    }

    try:
        start = time.time()
        response = requests.post(url, json=payload, timeout=90)  # 90s in case Groq is busy
        elapsed = time.time() - start
    except Exception as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 200, f"Non-200 response: {response.text}"
    data = response.json()
    assert "answer" in data, "Missing 'answer' key in response"
    assert isinstance(data["answer"], str), "'answer' is not a string"
    assert len(data["answer"]) > 25, f"The answer seems too short: {data['answer'][:100]}"
    print("\n---")
    print("Groq Llama 3.1/3.3 70B Agent Response:")
    print(data["answer"])
    print(f"\nTime taken: {elapsed:.1f} seconds\n")
    print("Test passed: Language Agent (Groq Llama-3) /analyze endpoint is working.")

if __name__ == "__main__":
    test_language_agent_analyze()
