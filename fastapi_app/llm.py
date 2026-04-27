import json
import logging
import os

from config import model_name
from httpx import RequestError
from openai import APIStatusError, Client
from pydantic import BaseModel, ValidationError
from schemas import JobExtractionSchema, JobListingSchema, JobMatchAssessment
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

logger = logging.getLogger(__name__)


class LLM:
    def __init__(self, provider: str) -> None:
        match provider:
            case "ollama":
                self.client = Client(
                    base_url=os.getenv("OLLAMA_URL"),
                    api_key="not_required_for_ollama",
                    timeout=120,
                )
                logger.info("Ollama client initialized.")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(3),
        retry=retry_if_exception_type((RequestError, OSError)),
        before_sleep=before_sleep_log(logger, logging.INFO),
    )
    def get_listings_details(
        self, job_listing: JobListingSchema, system_instruction: str
    ):
        """
        Extracts structured job details from scraped listing text using the LLM.

        Sends the job listing's text content to the LLM with a system instruction prompt.
        The LLM returns structured data (title, company, experience, salary, etc.) which
        is validated and returned as a JobListingSchema.

        Args:
            job_listing: JobListingSchema containing the scraped text content and metadata.
            system_instruction: System prompt instructing the LLM on extraction format.

        Returns:
            JobListingSchema with extracted and validated job details.

        Raises:
            RuntimeError: If there is an error calling the LLM API or decoding the response.
        """
        logger.info("DEBUG: LLM - Starting get_listings_details() to ollama model")
        text_content = job_listing.text_content if job_listing.text_content else ""
        data = self._make_llm_call(
            (system_instruction, text_content), JobExtractionSchema
        )
        return JobListingSchema(**data)

    def analyze_job_fit(self, job_instance: JobListingSchema, resume_pl, resume_en):
        """
        Analyzes a Django JobListing against a resume using Ollama.
        """
        prompts = self._generate_matching_prompt(job_instance, resume_pl, resume_en)
        data = self._make_llm_call(prompts, JobMatchAssessment)
        # This returns the validated Pydantic object
        return JobMatchAssessment(**data)

    def _generate_matching_prompt(
        self, job_instance: JobListingSchema, resume_pl, resume_en
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
            "Your sole job in this turn is to evaluate candidate-job fit with precision and skepticism. "
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

    def _make_llm_call(self, prompts: tuple[str, str], schema: type[BaseModel]) -> dict:
        try:
            # Call the local Ollama instance
            logger.debug("Sending chat request to Ollama with model: %s", "llama3.2")
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": f"{prompts[0]}",
                    },
                    {"role": "user", "content": prompts[1]},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            logger.debug(f"DEBUG: {response.choices}")
            # Extract the text content from the Ollama response
            # response_text = response.get("message", {}).get("content", "")
            response_content = response.choices[0].message.content
            logger.info("LLM raw response: %s", response_content)
            try:
                data = schema.model_validate_json(
                    response_content if response_content else ""
                )
                logger.debug("Validated model: %s", data.model_dump())
                return data.model_dump()
            except ValidationError as e:
                errors = e.errors()
                error_summary = [
                    f"{err['loc']}: {err['msg']} (input: {repr(err.get('input'))})"
                    for err in errors
                ]
                context = f"Schema={schema.__name__}, Response={response_content if response_content else ''}"
                detail = f"{len(errors)} validation error(s): {error_summary}. Context: {context}"
                logger.error("LLM validation failed. %s", detail)
                raise ValueError(
                    f"LLM response failed schema validation. {detail}"
                ) from e
            except Exception as e:
                logger.error("Unexpected error during schema validation: %s", e)
                raise RuntimeError(
                    f"Unexpected error during schema validation: {e}"
                ) from e

        except APIStatusError as e:
            raise RuntimeError(f"Error calling Ollama API: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Error decoding JSON response from Ollama API: {e}"
            ) from e
