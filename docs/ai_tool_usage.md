# AI Tool Usage

This document describes how to use the Finance AI Agent, both via the web UI and API endpoints.

## Using the Streamlit Web App

1. **Access the Web App**
   - Navigate to the deployed Streamlit link (e.g., [https://nikhil-9981-finance-ai-agent-streamlit-appapp-5sxfhl.streamlit.app/](#)).

2. **Submit Your Query**
   - Type a finance question into the text box (e.g., _"What’s our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"_)
   - Alternatively, upload an audio file (WAV/MP3) or use the microphone feature if enabled.

3. **View the Results**
   - The app displays the market brief as text.
   - If using text mode, the answer is also read aloud using text-to-speech.

4. **Typical Supported Queries**
   - "Get the latest price and risk analysis for AAPL, MSFT, and TSM."
   - "Show recent SEC filings for Tesla."
   - "Summarize earnings surprises for US tech stocks."

## Using API Endpoints

Each microservice exposes a documented API. Example usage:

- **API Agent**
    ```
    POST /quote
    {
      "symbols": ["AAPL", "TSM"],
      "history": true,
      "info": true
    }
    ```
- **Scraper Agent**
    ```
    POST /filing
    {
      "cik": "0000320193", "filing_type": "10-K"
    }
    ```
- **Orchestrator Agent**
    ```
    POST /orchestrate
    {
      "question": "Summarize Apple and Nvidia's latest financials."
    }
    ```

## Notes

- For live market data, ensure your AlphaVantage API key is valid.
- The accuracy of ticker extraction and SEC filing lookups depends on LLM extraction and data mappings.
- Voice features may vary in quality; text mode is recommended for critical queries.

