"""
AI Service Module
Handles AI-related business logic:
- Prompt composition (three-layer design)
- AI API calls (Gemini or Groq)
"""

import json
import re
from typing import Dict, Any
from config import AI_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL


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

    scoring_weightage_instructions = """
===ROLE CLASSIFICATION & SCORING WEIGHTAGE===

Before scoring, classify the role from the HR Query / Job Description as either "fresher" or "mid_senior".

CLASSIFICATION RULES:
- "fresher": Role targets fresh graduates, entry-level candidates, 0-2 years of experience, internship roles, trainee or junior positions, or roles where no prior work experience is required.
- "mid_senior/any experienced professional": Role requires 2+ years of work experience, specific domain skills, senior/lead/manager titles, or expects proven professional track record.
- If the JD is ambiguous or does not specify, default to "mid_senior".

SCORING WEIGHTAGE (apply this when computing score_percentage for each candidate):

  For FRESHER roles:
    - Education (degree, institution, GPA, relevant coursework):  80%
    - Projects & Internships (personal/academic projects, any internships): 20%

  For MID-SENIOR roles:
    - Skills (technical + domain skills matching the JD):          50%
    - Work Experience (years, relevance, seniority of past roles): 45%
    - Location (proximity or match to job location if specified):   5%

IMPORTANT:
- Score each candidate strictly using these weights. A candidate weak in a high-weight category cannot compensate with a strong low-weight category.
- In the "strengths" and "gaps" fields, explicitly mention whether the strength/gap is in a high-weight or low-weight category so the HR team understands its impact on the score.
- The "role_type" field in the output must reflect your classification: either "fresher" or "mid_senior".
"""

    schema_instructions = """
Expected JSON output schema:
{
  "role_type": "fresher" | "mid_senior",
  "candidates": [
    {
      "id": "<R-XXX>",
      "name": "Candidate Name (as per the resume)",
      "score_percentage": 85,
      "is_suitable": true,
      "strengths": ["..."],
      "gaps": ["..."],
      "evidence": ["..."]
    }
   ],
  "ranking": ["R-002","R-001"],
  "jd_fit_summary": "..."
}

CRITICAL INSTRUCTION FOR "jd_fit_summary":
- Keep it EXTREMELY brief: 1-2 sentences maximum.
- Focus ONLY on the overall candidate pool quality and key gaps/strengths common across ALL candidates.
- DO NOT mention individual candidate names or IDs (R-001, R-002, etc.).
- Example: "Most candidates demonstrate strong technical backgrounds but lack the required 5+ years of leadership experience. The candidate pool shows solid project management skills but limited exposure to cloud technologies."
"""

    resume_context = _build_resume_context(parsed_resumes)

    hr_query_section = (
        f"HR Query / Job Description:\n{jd_text.strip()}\n"
        if jd_text and jd_text.strip()
        else "HR Query / Job Description:\n\n"
    )

    prompt = "\n\n".join([
        "===SYSTEM_INSTRUCTIONS===",
        system_instructions,
        scoring_weightage_instructions,
        "===OUTPUT_SCHEMA===",
        schema_instructions,
        "===RESUME_CONTEXT===",
        resume_context,
        "===HR_QUERY===",
        hr_query_section,
        "===TASK===",
        (
            "Step 1: Read the HR Query and classify the role as 'fresher' or 'mid_senior' using the classification rules above. "
            "Step 2: Apply the corresponding scoring weightage to evaluate each candidate. "
            "Step 3: Return a single JSON object matching the schema exactly. "
            "For each strength/gap include a one-line evidence snippet and note whether it is in a high-weight or low-weight category."
        )
    ])

    return prompt


# ============================================================================
# AI API CLIENTS
# ============================================================================

def _call_gemini_api(prompt: str) -> Dict[str, Any]:
    """Call Gemini 2.5 Flash API and return parsed JSON response."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json",
            )
        )

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Strip markdown code fences if the model wraps output in them
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
            response_text = re.sub(r"\s*```$", "", response_text).strip()

        return json.loads(response_text)

    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


def _call_groq_api(prompt: str) -> Dict[str, Any]:
    """Call Groq API and return parsed JSON response."""
    try:
        from groq import Groq

        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        response_text = response.choices[0].message.content.strip()

        # Strip markdown code fences if the model wraps output in them
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
            response_text = re.sub(r"\s*```$", "", response_text).strip()

        return json.loads(response_text)

    except Exception as e:
        raise Exception(f"Groq API error: {str(e)}")


def get_ai_response(prompt: str, parsed_resumes: Dict[str, str]) -> Dict[str, Any]:
    """
    Send the composed prompt to the configured AI provider and return the structured response.

    Args:
        prompt: The structured prompt to send
        parsed_resumes: The parsed resume data (kept for interface consistency)

    Returns:
        Dict containing structured JSON response with candidates, ranking, etc.

    Raises:
        ValueError: If API key is not configured
        Exception: If the API call fails
    """
    if AI_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. Add it to your .env file.\n"
                "Get your key at: https://console.groq.com/keys"
            )
        return _call_groq_api(prompt)
    
    elif AI_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. Add it to your .env file.\n"
                "Get your key at: https://aistudio.google.com/app/apikey"
            )
        return _call_gemini_api(prompt)
    
    else:
        raise ValueError(
            f"Invalid AI_PROVIDER: {AI_PROVIDER}. Must be 'gemini' or 'groq'.\n"
            "Update AI_PROVIDER in your .env file."
        )


# Legacy function name for backward compatibility
def get_gemini_response(prompt: str, parsed_resumes: Dict[str, str]) -> Dict[str, Any]:
    """
    Legacy function name - routes to get_ai_response.
    Kept for backward compatibility with existing code.
    """
    return get_ai_response(prompt, parsed_resumes)


# ============================================================================
# RESPONSE FORMATTER
# ============================================================================

def format_response_to_text(json_response: Dict[str, Any], filter_type: str = "all") -> str:
    """
    Convert the JSON response into a clean plain-text report for download.
    Internal IDs (R-001, R-002, etc.) are never shown to the user.

    Args:
        json_response: Structured JSON from the AI model.
        filter_type:   "all"          → full report (default)
                       "suitable"     → suitable candidates only
                       "not_suitable" → not-suitable candidates only
    """
    if not json_response or "candidates" not in json_response:
        return "No analysis results available."

    output_lines = []

    output_lines.append("=" * 80)
    output_lines.append("RESUME SCREENING ANALYSIS REPORT")
    if filter_type == "suitable":
        output_lines.append("[ SUITABLE CANDIDATES ONLY ]")
    elif filter_type == "not_suitable":
        output_lines.append("[ NOT SUITABLE CANDIDATES ONLY ]")
    output_lines.append("=" * 80)
    output_lines.append("")

    # Role type & weightage
    role_type = json_response.get("role_type", "").lower()
    if role_type == "fresher":
        output_lines.append("ROLE TYPE : FRESHER")
        output_lines.append("Scoring Weightage:")
        output_lines.append("  Education               -> 80%  (high priority)")
        output_lines.append("  Projects & Internships  -> 20%")
        output_lines.append("")
    elif role_type == "mid_senior":
        output_lines.append("ROLE TYPE : MID / SENIOR")
        output_lines.append("Scoring Weightage:")
        output_lines.append("  Skills                  -> 50%  (high priority)")
        output_lines.append("  Work Experience         -> 45%  (high priority)")
        output_lines.append("  Location                ->  5%")
        output_lines.append("")

    # Overall summary only in full report
    if filter_type == "all" and "jd_fit_summary" in json_response:
        output_lines.append("OVERALL SUMMARY")
        output_lines.append("-" * 80)
        output_lines.append(json_response["jd_fit_summary"])
        output_lines.append("")

    output_lines.append("DETAILED CANDIDATE ANALYSIS")
    output_lines.append("=" * 80)
    output_lines.append("")

    all_candidates = json_response.get("candidates", [])
    ranking = json_response.get("ranking", [])

    candidate_map = {c.get("id"): c for c in all_candidates}
    ranked_candidates = [candidate_map[cid] for cid in ranking if cid in candidate_map]
    for c in all_candidates:
        if c not in ranked_candidates:
            ranked_candidates.append(c)

    # Assign overall rank numbers before filtering
    for i, c in enumerate(ranked_candidates):
        c["_rank_txt"] = i + 1

    if filter_type == "suitable":
        ranked_candidates = [c for c in ranked_candidates if c.get("is_suitable", False)]
    elif filter_type == "not_suitable":
        ranked_candidates = [c for c in ranked_candidates if not c.get("is_suitable", False)]

    for candidate in ranked_candidates:
        rank_num = candidate.get("_rank_txt", "?")
        name = candidate.get("name", "Name not found in resume")
        score = candidate.get("score_percentage", 0)
        is_suitable = candidate.get("is_suitable", False)

        output_lines.append(f"Rank #{rank_num}")
        output_lines.append(f"  Candidate   : {name}")
        output_lines.append(f"  Match Score : {score}%")
        output_lines.append(f"  Status      : {'SUITABLE FOR ROLE' if is_suitable else 'NOT SUITABLE FOR ROLE'}")
        output_lines.append("")

        strengths = candidate.get("strengths", [])
        if strengths:
            output_lines.append("  Key Strengths:")
            for s in strengths:
                output_lines.append(f"    * {s}")
            output_lines.append("")

        gaps = candidate.get("gaps", [])
        if gaps:
            output_lines.append("  Areas of Concern:")
            for g in gaps:
                output_lines.append(f"    * {g}")
            output_lines.append("")

        evidence = candidate.get("evidence", [])
        if evidence:
            output_lines.append("  Supporting Evidence:")
            for ev in evidence[:3]:
                output_lines.append(f"    * \"{ev}\"")
            output_lines.append("")

        output_lines.append("-" * 80)
        output_lines.append("")

    output_lines.append("=" * 80)
    output_lines.append("END OF REPORT")
    output_lines.append("=" * 80)

    return "\n".join(output_lines)
