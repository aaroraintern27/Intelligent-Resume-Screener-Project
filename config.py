"""
Configuration Module
Centralized environment configuration for the application.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ============================================================================
# RESUME LIMITS
# ============================================================================

# Gemini 2.5 Flash has a 1M token context window — 20 resumes is a safe limit.
MAX_RESUMES = int(os.getenv("MAX_RESUMES", "20"))
