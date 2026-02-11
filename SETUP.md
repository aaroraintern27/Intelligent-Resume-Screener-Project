# Intelligent Resume Screener - Setup Guide

## Quick Start with Groq API (Current Setup)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Then edit `.env` and add your Groq API key:

```env
AI_PROVIDER=groq
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

### 3. Run the Application

```bash
streamlit run app.py
```

---

## How to Get Groq API Key

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste it into your `.env` file

---

## Switching to Gemini (Future)

When you receive the Gemini API key and model name:

1. Update `.env`:
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-pro
   ```

2. Update `requirements.txt` - uncomment the line:
   ```
   google-generativeai
   ```

3. Install the new dependency:
   ```bash
   pip install google-generativeai
   ```

4. Restart the application

---

## Architecture Overview

### File Structure
```
config.py           → Environment configuration (API keys, settings)
resume_parser.py    → Document parsing (PDF text extraction)
ai_service.py       → AI business logic (prompt building + API calls)
app.py              → Streamlit UI (presentation layer)
```

### Data Flow
```
User Upload PDFs
    ↓
resume_parser.py → Extracts text → {"R-001": "text...", "R-002": "text..."}
    ↓
ai_service.py → Composes 3-layer prompt (system + context + JD)
    ↓
ai_service.py → Calls Groq API (or Gemini when configured)
    ↓
Returns JSON: {"candidates": [...], "ranking": [...], "jd_fit_summary": "..."}
    ↓
app.py → Displays results in Streamlit UI
```

---

## Supported Models

### Groq (Current)
- `openai/gpt-oss-20b` (default)
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`
- `gemma2-9b-it`

To use a different Groq model, update `GROQ_MODEL` in `.env`

### Gemini (Future)
- `gemini-pro`
- `gemini-1.5-pro`
- Others as provided by your manager

---

## Troubleshooting

### Error: "No module named 'groq'"
Run: `pip install -r requirements.txt`

### Error: "GROQ_API_KEY not found"
Make sure you created `.env` file (not `.env.example`) and added your API key

### Error: "GROQ_API_KEY not configured"
1. Verify you created `.env` file (not `.env.example`)
2. Ensure `GROQ_API_KEY` is set with your actual API key
3. Get your API key from https://console.groq.com

### JSON parsing errors
The model might not be returning valid JSON. Check the console for the raw response.
