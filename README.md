# Intelligent Resume Screener

AI-powered resume screening application supporting both Google Gemini and Groq AI to analyze and rank candidates against job descriptions.

---

## Features

- **Bulk Processing**: Analyze up to 20 PDF resumes simultaneously
- **AI-Powered Analysis**: Choose between Google Gemini 2.5 Flash or Groq Llama 3.1
- **Smart Scoring**: Role-based weightage (Fresher vs. Mid/Senior)
- **Detailed Reports**: Match scores, strengths, gaps, and evidence
- **Export**: Download reports as text files

### Scoring System

**Fresher Roles** (0-2 years):
- Education: 80%
- Projects & Internships: 20%

**Mid/Senior Roles** (2+ years):
- Skills: 50%
- Experience: 45%
- Location: 5%

---

## Setup

### Prerequisites
- Python 3.8+
- API key for either:
  - **Google Gemini** ([Get one here](https://aistudio.google.com/app/apikey)) - Recommended
  - **Groq** ([Get one here](https://console.groq.com/keys)) - Free alternative

### Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   # Windows
   copy .env.example .env
   
   # macOS/Linux
   cp .env.example .env
   ```

3. **Configure your AI provider in `.env`**

   **Option A: Using Gemini (Recommended)**
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   MAX_RESUMES=20
   ```

   **Option B: Using Groq (Free Alternative)**
   ```env
   AI_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.1-70b-versatile
   MAX_RESUMES=20
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

   Opens at `http://localhost:8501`

---

## Usage

1. Upload PDF resumes (max 20)
2. Enter job description
3. Click "Analyze Resume"
4. Review results and download reports

---

## File Structure

```
├── config.py           # Configuration
├── resume_parser.py    # PDF text extraction
├── ai_service.py       # AI logic & Gemini API
├── app.py              # Streamlit UI
├── style.css           # Custom styling
└── requirements.txt    # Dependencies
```

---

## Tech Stack

- **Frontend**: Streamlit
- **AI Providers**: 
  - Google Gemini 2.5 Flash (recommended)
  - Groq Llama 3.1 70B (free alternative)
- **PDF Processing**: PyMuPDF
- **Configuration**: python-dotenv

---

## Troubleshooting

**Error: "GEMINI_API_KEY is not set" or "GROQ_API_KEY is not set"**
- Verify `.env` file exists (not `.env.example`)
- Check `AI_PROVIDER` matches the key you've provided
- Ensure API key is correct with no extra spaces
- Get keys from:
  - Gemini: [Google AI Studio](https://aistudio.google.com/app/apikey)
  - Groq: [Groq Console](https://console.groq.com/keys)

**Error: "Invalid AI_PROVIDER"**
- Set `AI_PROVIDER=gemini` or `AI_PROVIDER=groq` in `.env`

**PDF parsing errors**
- Ensure PDFs are not corrupted or password-protected

**API rate limit errors**
- Gemini: Wait a few minutes or check quota
- Groq: Free tier has rate limits, wait or upgrade

---

## Switching Between AI Providers

To switch providers, simply change the `AI_PROVIDER` value in your `.env` file:

```bash
# Switch to Gemini
AI_PROVIDER=gemini

# Switch to Groq
AI_PROVIDER=groq
```

Then restart the application. Make sure you have the corresponding API key configured!

---

## Security

⚠️ **Important**: 
- Never commit `.env` file (contains API keys)
- Keep API keys confidential
- `.gitignore` is configured to prevent accidental commits

---

## Requirements

```
streamlit>=1.28.0
pymupdf>=1.23.0
python-dotenv>=1.0.0
google-generativeai>=0.3.0  # For Gemini
groq>=0.4.0                 # For Groq
Pillow>=10.0.0
```
