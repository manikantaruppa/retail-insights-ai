"""
Insight Agent: Converts query results to natural language insights
"""
from typing import Dict, List, Optional
from src.agents.base_agent import BaseAgent
from src.utils.prompts import (
    INSIGHT_GENERATION_PROMPT,
    ERROR_EXPLANATION_PROMPT,
    format_query_results
)
from src.utils.logger import logger


class InsightAgent(BaseAgent):
    """Generates business insights from query results"""

    def __init__(self):
        super().__init__("InsightAgent")

    def generate_insight(
        self,
        user_question: str,
        sql_query: str,
        query_results: List[Dict]
    ) -> tuple[str, Dict]:
        """
        Generate natural language insight from query results

        Args:
            user_question: Original user question
            sql_query: SQL query that was executed
            query_results: Results from query execution

        Returns:
            tuple: (insight_text, token_usage)
        """
        try:
            logger.info(f"Generating insight for results")

            # Format results for prompt
            results_str = format_query_results(query_results, max_rows=20)

            # Generate insight
            prompt = INSIGHT_GENERATION_PROMPT.format(
                user_question=user_question,
                sql_query=sql_query,
                query_results=results_str
            )

            insight, token_usage = self.generate_response(
                prompt=prompt,
                temperature=0.3  # Slightly higher for natural language
            )

            logger.info(f"Generated insight: {len(insight)} characters")

            return insight.strip(), token_usage

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            raise

    def generate_error_explanation(
        self,
        user_question: str,
        error_type: str,
        error_message: str
    ) -> tuple[str, Dict]:
        """
        Generate user-friendly error explanation

        Args:
            user_question: Original user question
            error_type: Type of error
            error_message: Technical error message

        Returns:
            tuple: (explanation, token_usage)
        """
        try:
            logger.info(f"Generating error explanation for: {error_type}")

            prompt = ERROR_EXPLANATION_PROMPT.format(
                user_question=user_question,
                error_type=error_type,
                error_message=error_message
            )

            explanation, token_usage = self.generate_response(
                prompt=prompt,
                temperature=0.5
            )

            return explanation.strip(), token_usage

        except Exception as e:
            logger.error(f"Error explanation generation failed: {e}")
            # Fallback to basic error message
            fallback = (
                f"I encountered an error while processing your question. "
                f"Error: {error_message}. "
                f"Please try rephrasing your question."
            )
            return fallback, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


__all__ = ['InsightAgent']
