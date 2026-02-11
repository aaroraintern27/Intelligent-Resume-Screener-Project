"""
Configuration Module
Centralized environment configuration for the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# ============================================================================
# AI PROVIDER CONFIGURATION
# ============================================================================

# AI Provider: 'groq' or 'gemini'
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").lower()


# ============================================================================
# GROQ CONFIGURATION
# ============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")


# ============================================================================
# RESUME LIMITS (based on model context)
# ============================================================================

# For openai/gpt-oss-20b (8k context): max 2-3 resumes safely
# For larger context models (32k+): increase this limit accordingly
MAX_RESUMES = 3
