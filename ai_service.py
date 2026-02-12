"""
AI Service Module
Handles AI-related business logic:
- Prompt composition (three-layer design)
- AI model client calls (Groq/Gemini)
"""

import json
from typing import Dict, Any
from config import (
    AI_PROVIDER,
    GROQ_API_KEY,
    GROQ_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL
)


# ============================================================================
# PROMPT BUILDING
# ============================================================================

def _build_resume_context(parsed_resumes: Dict[str, str]) -> str:
    """
    Build the resume context section with clear separators and JSON identifier.
    Uses the fixed output pattern R-001, R-002, ... as keys.
    """
    blocks = []
    for rid, text in parsed_resumes.items():
        # Separator includes a small JSON with identifier
        sep_start = f"===CANDIDATE_START {json.dumps({'id': rid})} ==="
        sep_end = "===CANDIDATE_END==="
        blocks.append(f"{sep_start}\n{text}\n{sep_end}")
    return "\n\n".join(blocks)


def compose_prompt(parsed_resumes: Dict[str, str], jd_text: str) -> str:
    """
    Compose the full structured prompt to send to Gemini.
    The prompt uses a three-layer design:
      1) System instruction (behavior + rules)
      2) Resume context (parsed text with separators)
      3) HR query / Job Description

    The model is instructed to return a JSON object with a specific schema.
    """
    system_instructions = """
You are an AI Resume Screening Assistant for HR. Follow these rules:
- Be objective and grounded: do not assume or invent skills, experiences, or qualifications not explicitly present in the provided resume texts.
- When you make any claim about a candidate in the strengths/gaps/evidence fields, include a short quoted excerpt that supports the claim.
- The IDs (R-001, R-002, etc.) are ONLY for internal system tracking. DO NOT mention these IDs in the "jd_fit_summary", "name", "score_percentage", "is_suitable", "strengths", "gaps", "evidence" field.
- Output MUST be valid JSON (no extra commentary). Use the schema requested below.
- Keep answers concise and focused on the job description / query provided.
"""

    schema_instructions = """
Expected JSON output schema:
{
  "candidates": [
    {
      "id": "<R-XXX>",
      "name": "Candidate Name (as per the resume)",
      "score_percentage": 85,      # percentage fit score (0-100)
      "is_suitable": true,         # true if score >= 70%, false otherwise
      "strengths": ["..."],        # list of short strings (each with an evidence snippet)
      "gaps": ["..."],             # list of short strings (each with an evidence snippet)
      "evidence": ["..."]          # list of quoted excerpts from the resume supporting the score
    }
  ],
  "ranking": ["R-002","R-001"],    # array of candidate ids ordered best->worst (highest score first)
  "jd_fit_summary": "..."          # OVERALL summary for ALL candidates combined (2-4 sentences). Use candidate NAMES or generic terms (e.g., "the top candidates", "strongest applicants"). NEVER use IDs like R-001, R-002 in this summary.
}
"""

    resume_context = _build_resume_context(parsed_resumes)

    hr_query_section = f"HR Query / Job Description:\n{jd_text.strip()}\n" if jd_text and jd_text.strip() else "HR Query / Job Description:\n\n"

    prompt = "\n\n".join([
        "===SYSTEM_INSTRUCTIONS===",
        system_instructions,
        "===OUTPUT_SCHEMA===",
        schema_instructions,
        "===RESUME_CONTEXT===",
        resume_context,
        "===HR_QUERY===",
        hr_query_section,
        "===TASK===",
        "Analyze the candidates above against the HR Query. Return a JSON object matching the schema exactly. For each strength/gap include a one-line evidence snippet."
    ])

    return prompt


# ============================================================================
# AI CLIENT (Groq / Gemini)
# ============================================================================

def _call_groq_api(prompt: str) -> Dict[str, Any]:
    """Call Groq API using the Groq Python SDK."""
    try:
        from groq import Groq
        
        client = Groq(api_key=GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=3072,
            response_format={"type": "json_object"}
        )
        
        response_text = completion.choices[0].message.content
        return json.loads(response_text)
        
    except Exception as e:
        raise Exception(f"Groq API error: {str(e)}")


def _call_gemini_api(prompt: str) -> Dict[str, Any]:
    """Call Gemini API (placeholder for future implementation)."""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        response = model.generate_content(prompt)
        return json.loads(response.text)
        
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


def get_ai_response(prompt: str, parsed_resumes: Dict[str, str]) -> Dict[str, Any]:
    """
    Sends the composed prompt to the configured AI provider (Groq or Gemini).
    
    Args:
        prompt: The structured prompt to send
        parsed_resumes: The parsed resume data (not used but kept for backward compatibility)
    
    Returns:
        Dict containing structured JSON response with candidates, ranking, etc.
    
    Raises:
        ValueError: If no API key is configured for the selected provider
        Exception: If API call fails
    """
    # Route to appropriate provider
    if AI_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not configured. Please set it in your .env file.\n"
                "Get your API key from: https://console.groq.com"
            )
        return _call_groq_api(prompt)
    
    elif AI_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not configured. Please set it in your .env file."
            )
        return _call_gemini_api(prompt)
    
    else:
        raise ValueError(
            f"Unknown AI provider: '{AI_PROVIDER}'. "
            "Valid options are: 'groq' or 'gemini'"
        )


def format_response_to_text(json_response: Dict[str, Any]) -> str:
    """
    Convert JSON response from AI model to human-readable text format.
    Internal IDs (R-001, R-002, etc.) are hidden from users.
    
    Args:
        json_response: The structured JSON response from the AI model
    
    Returns:
        Formatted string with all analysis details (no internal IDs shown)
    """
    if not json_response or "candidates" not in json_response:
        return "No analysis results available."
    
    output_lines = []
    
    # Header
    output_lines.append("=" * 80)
    output_lines.append("RESUME SCREENING ANALYSIS REPORT")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # Overall Summary (for all candidates)
    if "jd_fit_summary" in json_response:
        output_lines.append("📋 OVERALL SUMMARY")
        output_lines.append("-" * 80)
        output_lines.append(json_response["jd_fit_summary"])
        output_lines.append("")
    
    # Detailed candidate analysis (sorted by ranking)
    output_lines.append("👥 DETAILED CANDIDATE ANALYSIS")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    candidates = json_response.get("candidates", [])
    ranking = json_response.get("ranking", [])
    
    # Create a map of ID to candidate for easy lookup
    candidate_map = {c.get("id"): c for c in candidates}
    
    # Iterate through ranking to maintain order (best to worst)
    ranked_candidates = []
    for cid in ranking:
        if cid in candidate_map:
            ranked_candidates.append(candidate_map[cid])
    
    # Add any candidates not in ranking (shouldn't happen but safe fallback)
    for candidate in candidates:
        if candidate not in ranked_candidates:
            ranked_candidates.append(candidate)
    
    # Display each candidate (no R-001 IDs shown)
    for rank_num, candidate in enumerate(ranked_candidates, 1):
        name = candidate.get("name", "Name not found in resume")
        score = candidate.get("score_percentage", 0)
        is_suitable = candidate.get("is_suitable", False)
        
        # Candidate header (no ID shown to user)
        output_lines.append(f"🏆 Rank #{rank_num}")
        output_lines.append(f"   Candidate: {name}")
        output_lines.append(f"   Match Score: {score}%")
        output_lines.append(f"   Status: {'✅ SUITABLE FOR ROLE' if is_suitable else '❌ NOT SUITABLE FOR ROLE'}")
        output_lines.append("")
        
        # Strengths
        strengths = candidate.get("strengths", [])
        if strengths:
            output_lines.append("   💪 Key Strengths:")
            for strength in strengths:
                output_lines.append(f"      • {strength}")
            output_lines.append("")
        
        # Gaps
        gaps = candidate.get("gaps", [])
        if gaps:
            output_lines.append("   ⚠️  Areas of Concern:")
            for gap in gaps:
                output_lines.append(f"      • {gap}")
            output_lines.append("")
        
        # Evidence
        evidence = candidate.get("evidence", [])
        if evidence:
            output_lines.append("   📌 Supporting Evidence:")
            for ev in evidence[:3]:  # Show top 3 evidence points
                output_lines.append(f"      • \"{ev}\"")
            output_lines.append("")
        
        output_lines.append("-" * 80)
        output_lines.append("")
    
    output_lines.append("=" * 80)
    output_lines.append("END OF REPORT")
    output_lines.append("=" * 80)
    
    return "\n".join(output_lines)


# Backward compatibility alias
get_gemini_response = get_ai_response
