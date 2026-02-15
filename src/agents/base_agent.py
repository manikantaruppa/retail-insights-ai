"""
Base agent class with Gemini integration using new google.genai package
"""
from typing import Optional, Dict, List
from google import genai
from google.genai import types
from src.config import Config
from src.utils.logger import logger


class LLMError(Exception):
    """Custom exception for LLM errors"""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class BaseAgent:
    """Base class for all agents with multi-model fallback"""

    # Gemini models to try in order (verified working models)
    GEMINI_MODELS = [
        # Tier 1: Fastest, lightest (best for free tier quota)
        "models/gemini-2.0-flash-lite",
        "models/gemini-2.0-flash-lite-001",

        # Tier 2: Balanced speed/capability (recommended)
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-001",
        "models/gemini-2.5-flash",

        # Tier 3: Experimental
        "models/gemini-exp-1206",

        # Tier 4: Most capable
        "models/gemini-2.5-pro",

        # Tier 5: Legacy fallback
        "models/gemini-1.5-flash-002",
        "models/gemini-1.5-flash-8b",
        "models/gemini-1.5-pro-002",
    ]

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.token_count = {"input": 0, "output": 0}
        self.last_successful_model: Optional[str] = None
        self.failed_models = set()
        logger.info(f"Initialized {agent_name} with google.genai")

    def generate_response(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> tuple[str, Dict]:
        """
        Generate response using Gemini with multi-model fallback

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum output tokens (default: 2048)

        Returns:
            tuple: (response_text, token_usage)
        """
        # Set reasonable default max_tokens if not specified
        if max_tokens is None:
            max_tokens = 2048  # Generous default

        # Configuration
        config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            top_k=40,
            max_output_tokens=max_tokens
        )

        # Try models in order
        models_to_try = self._get_models_to_try()
        last_error = None
        attempts = 0

        for model_name in models_to_try:
            if model_name in self.failed_models:
                continue

            attempts += 1

            try:
                logger.debug(f"[{self.agent_name}] Trying {model_name}...")

                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )

                # Extract response text - FIXED METHOD
                response_text = self._extract_text_from_response(response)

                if not response_text or response_text == "None":
                    logger.warning(
                        f"[{self.agent_name}] {model_name} returned empty/None response "
                        f"(finish_reason: {self._get_finish_reason(response)})"
                    )
                    continue

                # Extract token usage
                token_usage = self._extract_token_usage(response, prompt)

                # Update cumulative count
                self.token_count["input"] += token_usage["input_tokens"]
                self.token_count["output"] += token_usage["output_tokens"]

                # Remember successful model
                self.last_successful_model = model_name

                logger.info(
                    f"[{self.agent_name}] ✅ {model_name}: "
                    f"{token_usage['total_tokens']} tokens"
                )

                return response_text, token_usage

            except Exception as e:
                error_msg = str(e)
                last_error = e

                if "404" in error_msg or "not found" in error_msg.lower():
                    logger.warning(f"[{self.agent_name}] {model_name} not found (404)")
                    self.failed_models.add(model_name)

                elif "429" in error_msg or "quota" in error_msg.lower():
                    logger.warning(f"[{self.agent_name}] {model_name} quota exhausted (429)")
                    # Don't mark as permanently failed

                elif "400" in error_msg:
                    logger.warning(f"[{self.agent_name}] {model_name} invalid request (400)")
                    self.failed_models.add(model_name)

                else:
                    logger.warning(f"[{self.agent_name}] {model_name} error: {error_msg[:100]}")

                continue

        # All models failed
        error_detail = (
            f"All {attempts} models failed. Last error: {last_error}. "
            f"Check API key or quota at https://aistudio.google.com"
        )
        logger.error(f"[{self.agent_name}] {error_detail}")
        raise LLMError(detail=error_detail)

    def _extract_text_from_response(self, response) -> Optional[str]:
        """
        Extract text from Gemini response - handles multiple response formats
        """
        # Method 1: Direct text attribute (preferred)
        if hasattr(response, 'text') and response.text and response.text != "None":
            return str(response.text).strip()

        # Method 2: Through candidates (fallback)
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content

                    # Check if content has parts
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'text') and part.text:
                                return str(part.text).strip()

        # Method 3: Check parts directly on response
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    return str(part.text).strip()

        return None

    def _get_finish_reason(self, response) -> str:
        """Get finish reason from response for debugging"""
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    return str(candidate.finish_reason)
        except:
            pass
        return "UNKNOWN"

    def _get_models_to_try(self) -> List[str]:
        """Get ordered list of models to try"""
        if self.last_successful_model and self.last_successful_model not in self.failed_models:
            models = [self.last_successful_model]
            models.extend([m for m in self.GEMINI_MODELS if m != self.last_successful_model])
            return models
        return self.GEMINI_MODELS

    def _extract_token_usage(self, response, prompt: str) -> Dict:
        """Extract token usage from response"""
        try:
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                return {
                    "input_tokens": getattr(usage, 'prompt_token_count', 0),
                    "output_tokens": getattr(usage, 'candidates_token_count', 0),
                    "total_tokens": getattr(usage, 'total_token_count', 0)
                }
        except Exception as e:
            logger.warning(f"Could not extract token usage: {e}")

        # Fallback: estimate
        input_estimate = len(prompt) // 4
        output_estimate = 50  # Conservative estimate

        return {
            "input_tokens": input_estimate,
            "output_tokens": output_estimate,
            "total_tokens": input_estimate + output_estimate
        }

    def reset_token_count(self):
        """Reset token counter"""
        self.token_count = {"input": 0, "output": 0}

    def reset_failed_models(self):
        """Reset failed models list"""
        self.failed_models = set()
        logger.info(f"[{self.agent_name}] Reset failed models list")


__all__ = ['BaseAgent', 'LLMError']
