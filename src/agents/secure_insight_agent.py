"""
Secure Insight Agent with BigQuery AI-style privacy protection
Uses statistical summaries instead of raw data
"""
from typing import Dict, List
from src.agents.base_agent import BaseAgent
from src.utils.result_summarizer import ResultSummarizer
from src.utils.logger import logger


# Conversational Insight Prompt (BigQuery AI style)
CONVERSATIONAL_INSIGHT_PROMPT = """You are a friendly, knowledgeable data analyst having a conversation with a colleague about their sales data.

**Original Question:**
{user_question}

**SQL Query Executed:**
{sql_query}

**Statistical Summary** (NOT raw data - aggregated statistics only):
{statistical_summary}

**Instructions:**
Generate a conversational, natural response that:

1. **Starts naturally** with phrases like:
   - "Great question!"
   - "Interesting pattern here..."
   - "Let me break this down for you..."
   - "Looking at your data..."

2. **Highlights the key finding immediately**
   - Lead with the most important insight
   - Use concrete numbers

3. **Adds context and comparisons**
   - "nearly double"
   - "significant drop-off"
   - "far ahead of"
   - Percentages and ratios

4. **Points out interesting patterns**
   - Anomalies or surprises
   - Trends worth noting

5. **Suggests follow-up** (optional)
   - "Want to dive deeper into..."
   - "Curious about what's driving..."

6. **Style guidelines:**
   - Natural, conversational tone (like talking to a colleague)
   - 3-5 sentences maximum
   - No bullet points or lists
   - Use "your" (e.g., "your sales", "your top category")
   - Be enthusiastic but professional

**Example (Good):**
"Great question! Your Set category is absolutely dominating with $39.2M in revenue - that's nearly double the second-place Kurta category at $21.5M. Interestingly, there's a big drop-off after the top two, with Western Dress coming in at just $12.3M. Set alone accounts for almost half your total revenue, which suggests it might be worth investigating what's driving that success!"

**Example (Bad - Don't do this):**
"The query results show:
- Set: $39.2M
- Kurta: $21.5M
- Western Dress: $12.3M"

**Your conversational insight:**
"""

# Error handling prompt
ERROR_EXPLANATION_PROMPT = """An error occurred while processing the query.

**User Question:** {user_question}
**Error:** {error_message}

Generate a friendly, helpful response that:
1. Acknowledges the issue without technical jargon
2. Suggests how to rephrase the question
3. Offers alternative approaches

Keep it conversational and helpful.

Your response:
"""


class SecureInsightAgent(BaseAgent):
    """
    Generates insights from statistical summaries (not raw data)
    Implements BigQuery AI privacy model
    """

    def __init__(self):
        super().__init__("SecureInsightAgent")

    def generate_insight(
        self,
        user_question: str,
        sql_query: str,
        query_results: List[Dict]
    ) -> tuple[str, Dict]:
        """
        Generate conversational insight from query results

        **KEY PRIVACY FEATURE:**
        Converts raw results to statistical summary BEFORE sending to LLM
        LLM never sees individual records!

        Args:
            user_question: Original user question
            sql_query: SQL query executed
            query_results: Raw results from DuckDB

        Returns:
            tuple: (insight_text, token_usage)
        """
        try:
            logger.info(f"Generating secure insight (BigQuery AI style)")

            # 🔒 CRITICAL: Summarize results BEFORE sending to LLM
            summary = ResultSummarizer.summarize(query_results)

            # Format summary as text for LLM
            summary_text = ResultSummarizer.format_for_llm(summary)

            logger.info(
                f"Converted {len(query_results)} raw rows to "
                f"{summary['data_type']} summary for LLM"
            )

            # Generate conversational insight from SUMMARY (not raw data!)
            prompt = CONVERSATIONAL_INSIGHT_PROMPT.format(
                user_question=user_question,
                sql_query=sql_query,
                statistical_summary=summary_text
            )

            insight, token_usage = self.generate_response(
                prompt=prompt,
                temperature=0.4  # Slightly higher for natural conversation
            )

            logger.info(f"Generated conversational insight: {len(insight)} characters")

            return insight.strip(), token_usage

        except Exception as e:
            logger.error(f"Secure insight generation failed: {e}")
            raise

    def generate_error_explanation(
        self,
        user_question: str,
        error_type: str,
        error_message: str
    ) -> tuple[str, Dict]:
        """Generate friendly error explanation"""
        try:
            logger.info(f"Generating error explanation for: {error_type}")

            prompt = ERROR_EXPLANATION_PROMPT.format(
                user_question=user_question,
                error_message=error_message
            )

            explanation, token_usage = self.generate_response(
                prompt=prompt,
                temperature=0.5
            )

            return explanation.strip(), token_usage

        except Exception as e:
            logger.error(f"Error explanation generation failed: {e}")
            # Fallback
            fallback = (
                f"I encountered an issue processing your question. "
                f"Try rephrasing it or asking about aggregated metrics "
                f"like totals, averages, or counts instead of individual records."
            )
            return fallback, {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


__all__ = ['SecureInsightAgent']
