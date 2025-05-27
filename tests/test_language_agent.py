import requests
import time

def test_language_agent_analyze():
    """
    Test the /analyze endpoint (RAG LLM, e.g., Groq Llama 3.1/3.3 70B).
    """
    url = "http://localhost:8004/analyze"
    payload = {
        "question": "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
    }
    
    try:
        start = time.time()
        response = requests.post(url, json=payload, timeout=90)
        elapsed = time.time() - start
        assert response.status_code == 200, f"Non-200 response: {response.text}"
        data = response.json()
        assert "answer" in data, "Missing 'answer' key in response"
        assert isinstance(data["answer"], str), "'answer' is not a string"
        assert len(data["answer"]) > 25, f"Answer too short: {data['answer'][:100]}"
        print("\n---\nGroq Llama 3.x /analyze Response:")
        print(data["answer"])
        print(f"\nTime taken: {elapsed:.1f} seconds\n")
        print("✅ /analyze endpoint test passed.")
    except Exception as e:
        print(f"❌ /analyze endpoint test failed: {e}")
        assert False, f"Test failed: {e}"

def test_language_agent_analyze_graph():
    """
    Test the /analyze_graph endpoint (LangGraph multi-agent orchestration).
    """
    url = "http://localhost:8004/analyze_graph"
    payload = {
        "question": "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
    }
    try:
        response = requests.post(url, json=payload, timeout=90)
        assert response.status_code == 200, f"Non-200 response: {response.text}"
        data = response.json()
        assert "answer" in data, "Missing 'answer' in response"
        assert isinstance(data["answer"], str)
        print("\n---\nLangGraph /analyze_graph Response:")
        print(data["answer"])
        print("✅ /analyze_graph endpoint test passed.")
    except Exception as e:
        print(f"❌ /analyze_graph endpoint test failed: {e}")
        assert False, f"Test failed: {e}"

def test_language_agent_analyze_simple():
    """
    Test the /analyze_simple endpoint (vanilla RAG pipeline).
    """
    url = "http://localhost:8004/analyze_simple"
    payload = {
        "question": "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
    }
    try:
        response = requests.post(url, json=payload, timeout=90)
        assert response.status_code == 200, f"Non-200 response: {response.text}"
        data = response.json()
        assert "answer" in data, "Missing 'answer' in response"
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 10, f"Answer too short: {data['answer'][:100]}"
        print("\n---\nRAG Baseline /analyze_simple Response:")
        print(data["answer"])
        print("✅ /analyze_simple endpoint test passed.")
    except Exception as e:
        print(f"❌ /analyze_simple endpoint test failed: {e}")
        assert False, f"Test failed: {e}"

if __name__ == "__main__":
    test_language_agent_analyze()
    test_language_agent_analyze_graph()
    test_language_agent_analyze_simple()
