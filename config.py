"""
Configuration Module
Centralized environment configuration for the application.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# AI PROVIDER CONFIGURATION
# ============================================================================

AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()  # "gemini" or "groq"


# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ============================================================================
# GROQ CONFIGURATION
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")


# ============================================================================
# RESUME LIMITS
# ============================================================================

# Both Gemini and Groq support large context windows — 20 resumes is a safe limit.
MAX_RESUMES = int(os.getenv("MAX_RESUMES", "20"))
