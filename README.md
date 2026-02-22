# Intelligent Resume Screener

AI-powered resume screening application using Google Gemini 2.5 Flash to analyze and rank candidates against job descriptions.

---

## Features

- **Bulk Processing**: Analyze up to 20 PDF resumes simultaneously
- **AI-Powered Analysis**: Uses Google Gemini 2.5 Flash
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
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

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

3. **Add your API key to `.env`**
   ```env
   GEMINI_API_KEY=your_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
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
- **AI**: Google Gemini 2.5 Flash
- **PDF Processing**: PyMuPDF
- **Configuration**: python-dotenv

---

## Troubleshooting

**Error: "GEMINI_API_KEY is not set"**
- Verify `.env` file exists (not `.env.example`)
- Check API key is correct with no extra spaces
- Get key from [Google AI Studio](https://aistudio.google.com/app/apikey)

**PDF parsing errors**
- Ensure PDFs are not corrupted or password-protected

**API rate limit errors**
- Wait a few minutes or check your API quota

---

## Security

⚠️ **Important**: 
- Never commit `.env` file (contains API key)
- Keep API keys confidential
- `.gitignore` is configured to prevent accidental commits

---

## Requirements

```
streamlit>=1.28.0
pymupdf>=1.23.0
python-dotenv>=1.0.0
google-generativeai>=0.3.0
Pillow>=10.0.0
```
