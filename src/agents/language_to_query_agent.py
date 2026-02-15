"""
Language-to-Query Agent: Converts natural language to SQL
"""
from typing import Dict, Optional
from src.agents.base_agent import BaseAgent
from src.utils.prompts import (
    SQL_GENERATION_PROMPT,
    CONFIDENCE_SCORING_PROMPT,
    format_schema_for_prompt,
    format_conversation_history
)
from src.utils.logger import logger


class LanguageToQueryAgent(BaseAgent):
    """Converts business questions to SQL queries"""

    def __init__(self):
        super().__init__("LanguageToQueryAgent")

    def generate_sql(
        self,
        user_question: str,
        schema: Dict[str, str],
        conversation_history: Optional[list] = None
    ) -> tuple[str, float, Dict]:
        """
        Generate SQL query from natural language question

        Args:
            user_question: User's natural language question
            schema: Database schema dictionary
            conversation_history: Previous conversation context

        Returns:
            tuple: (sql_query, confidence_score, token_usage)
        """
        try:
            logger.info(f"Generating SQL for: '{user_question}'")

            # Format schema and history
            schema_str = format_schema_for_prompt(schema)
            history_str = format_conversation_history(conversation_history or [])

            # Generate SQL query
            prompt = SQL_GENERATION_PROMPT.format(
                schema=schema_str,
                user_question=user_question,
                conversation_history=history_str
            )

            sql_query, token_usage = self.generate_response(
                prompt=prompt,
                temperature=0.1  # Low temperature for precise SQL
            )

            # Clean up response
            sql_query = sql_query.strip()

            # Remove markdown code blocks if present
            if sql_query.startswith("```"):
                lines = sql_query.split('\n')
                sql_query = '\n'.join(lines[1:-1]) if len(lines) > 2 else sql_query
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()

            # Get confidence score
            confidence_score = self._calculate_confidence(
                user_question, sql_query, schema
            )

            logger.info(f"Generated SQL (confidence: {confidence_score:.2f})")
            logger.debug(f"SQL: {sql_query}")

            return sql_query, confidence_score, token_usage

        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise

    def _calculate_confidence(
        self,
        user_question: str,
        sql_query: str,
        schema: Dict[str, str]
    ) -> float:
        """
        Calculate confidence score for generated SQL

        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        try:
            schema_str = format_schema_for_prompt(schema)

            prompt = CONFIDENCE_SCORING_PROMPT.format(
                user_question=user_question,
                sql_query=sql_query,
                schema=schema_str
            )

            response, _ = self.generate_response(
                prompt=prompt,
                temperature=0.0
            )

            # Extract numeric score
            score_str = response.strip().replace('\n', '').replace(' ', '')

            # Try to parse as float
            try:
                score = float(score_str)
                return max(0.0, min(1.0, score))  # Clamp to [0, 1]
            except ValueError:
                # If parsing fails, return medium confidence
                logger.warning(f"Could not parse confidence score: {score_str}")
                return 0.7

        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5  # Default medium confidence


__all__ = ['LanguageToQueryAgent']
