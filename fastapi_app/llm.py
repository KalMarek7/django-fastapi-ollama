import json
import logging
import os

from ollama import Client, ResponseError
from schemas import JobListingSchema

logger = logging.getLogger(__name__)


def generate_matching_prompt(
    job_instance: JobListingSchema, resume_pl, resume_en
) -> tuple[str, str]:
    # 1. Prepare the Job Metadata for the prompt
    job_metadata = f"""
    Title: {job_instance.title}
    Company: {job_instance.company}
    Required Experience: {job_instance.years_of_experience} years
    Salary Info: {job_instance.salary}
    Description: {job_instance.text_content[:2000] if job_instance.text_content else ""}
    """

    # 2. Construct the specialized Prompt
    system_prompt = (
        "You are a strict and analytical Technical Recruiter AI. "
        "You evaluate candidate-job fit with precision and skepticism. "
        "You NEVER inflate scores and you avoid defaulting to mid-range values. "
        "You must follow scoring rules strictly and output ONLY valid JSON."
    )

    user_prompt = f"""
    You must perform a STRICT, step-by-step comparison between job requirements and candidate skills.

    DO NOT guess or infer. ONLY use explicitly stated information.

    ---------------------
    PHASE 1 — EXTRACTION
    ---------------------

    Extract:

    1. REQUIRED_SKILLS:
    - Only skills that are clearly required in the job description
    - Ignore soft skills

    2. CANDIDATE_SKILLS:
    - Only skills explicitly mentioned in the resume (PL + EN combined)

    ---------------------
    PHASE 2 — COMPARISON (STRICT RULES)
    ---------------------

    Define:

    - MATCHED_SKILLS:
    Skills that appear EXACTLY in BOTH REQUIRED_SKILLS and CANDIDATE_SKILLS

    - MISSING_SKILLS:
    Skills that appear in REQUIRED_SKILLS but NOT in CANDIDATE_SKILLS

    STRICT RULES:
    - A skill MUST NOT appear in both lists
    - DO NOT infer similarity (e.g. Python ≠ Java, React ≠ Angular)
    - DO NOT include skills that are only in the resume
    - If unsure → treat as NOT matching

    ---------------------
    PHASE 3 — SCORING
    ---------------------

    Use:

    - Start at 100%
    - Subtract 15% for EACH missing required skill
    - Subtract 10–20% if experience is below requirement

    Clamp result between 0–100.

    ---------------------
    ANTI-BIAS RULE
    ---------------------
    Do NOT default to 60%. Use full range.

    ---------------------
    INPUT DATA
    ---------------------

    [JOB LISTING]
    {job_metadata}

    [RESUME PL]
    {resume_pl}

    [RESUME EN]
    {resume_en}

    ---------------------
    OUTPUT FORMAT (JSON ONLY)
    ---------------------

    Return ONLY:

    {{
    "match_percentage": integer,
    "experience_fit": "short explanation",
    "skill_alignment": [MATCHED_SKILLS],
    "missing_criteria": [MISSING_SKILLS],
    "verdict": "Should the candidate apply? One sentence."
    }}
    """
    return system_prompt, user_prompt


def make_llm_call(prompts: tuple[str, str], schema) -> dict:
    client = Client(host=os.getenv("OLLAMA_URL"), timeout=120)
    try:
        # Call the local Ollama instance
        logger.debug("Sending chat request to Ollama with model: %s", "llama3.2")
        response = client.chat(
            model="llama3.2",  # Specify your pulled Ollama model here
            messages=[
                {
                    "role": "system",
                    "content": f"{prompts[0]}",
                },
                {"role": "user", "content": prompts[1]},
            ],
            stream=False,  # Instructs Ollama to output standard JSON
            format=schema.model_json_schema(),
            options={"temperature": 0},
        )

        # Extract the text content from the Ollama response
        response_text = response.get("message", {}).get("content", "")

        logger.info("LLM raw response: %s", response_text)
        data = json.loads(response_text)
        logger.info("LLM clean data: %s", data)
        return data

    except ResponseError as e:
        raise RuntimeError(f"Error calling Ollama API: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding JSON response from Ollama API: {e}") from e
