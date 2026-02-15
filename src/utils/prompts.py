"""
Prompt templates for different agents
"""

# SQL Generation Prompts
SQL_GENERATION_PROMPT = """You are an expert SQL analyst for retail sales data. Convert the user's question into a valid SQL query.

**Database Schema:**
{schema}

**User Question:**
{user_question}

**Conversation History:**
{conversation_history}

**Instructions:**
1. Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP)
2. Use aggregations (GROUP BY, SUM, AVG) for large datasets
3. Always include relevant WHERE clauses for filtering
4. Use proper column names from the schema
5. Limit results to reasonable amounts (use LIMIT clause)
6. Handle date/time filtering appropriately
7. Use CTEs for complex queries if needed

**CRITICAL - Data Quality Handling:**
8. Real-world retail data often contains mixed types (e.g., "Stock", "N/A", empty strings in numeric columns)
9. **ALWAYS use TRY_CAST() instead of CAST()** for numeric conversions - this returns NULL for invalid values instead of failing
10. When aggregating numeric columns, filter out NULLs automatically (AVG/SUM ignore NULLs by default)
11. Example: Use `TRY_CAST(amount AS DECIMAL)` NOT `CAST(amount AS DECIMAL)`

**DuckDB-Specific:**
- TRY_CAST is supported in DuckDB
- Use DECIMAL or DOUBLE for numeric types
- VARCHAR for text columns

**Output Format:**
Return ONLY the SQL query, nothing else. No explanations, no markdown.

SQL Query:"""

# Validation Prompts
VALIDATION_PROMPT = """You are a SQL security validator. Analyze the following SQL query for safety and correctness.

**SQL Query:**
{sql_query}

**Database Schema:**
{schema}

**Validation Checks:**
1. Only SELECT statements allowed (no DDL/DML)
2. All referenced columns exist in schema
3. No SQL injection patterns
4. No dangerous operations (DROP, DELETE, etc.)
5. Syntax is valid
6. Aggregations are logically correct

**Output Format:**
Return a JSON object:
{{
    "valid": true/false,
    "issues": ["list of issues if any"],
    "corrected_query": "corrected SQL if needed, else null",
    "risk_level": "low/medium/high"
}}

Validation Result:"""

# Insight Generation Prompts
INSIGHT_GENERATION_PROMPT = """You are a business analyst interpreting retail sales data for executives.

**User Question:**
{user_question}

**SQL Query Executed:**
{sql_query}

**Query Results:**
{query_results}

**Instructions:**
1. Provide a clear, concise answer to the user's question
2. Highlight key insights and trends
3. Use business language (avoid technical jargon)
4. Include specific numbers and percentages
5. Mention any notable patterns or anomalies
6. Keep response under 150 words

**Output Format:**
Provide a natural language summary that directly answers the question.

Business Insight:"""

# Summarization Prompts
SUMMARIZATION_PROMPT = """You are an executive report writer analyzing retail sales data.

**Dataset Overview:**
- Total Records: {total_records}
- Date Range: {date_range}
- Data Source: {data_source}

**Key Metrics:**
{aggregated_metrics}

**Top Performers:**
{top_performers}

**Trends:**
{trends}

**Instructions:**
Generate a comprehensive executive summary (400-600 words) covering:
1. Overall performance highlights (with specific numbers)
2. Best performing categories/regions/products (top 3-5 with metrics)
3. Notable trends (growth/decline patterns)
4. Key opportunities or concerns (data-driven)
5. Actionable insights (specific recommendations)
6. Strategic implications for the business

Use clear, professional business language with specific metrics and insights.
Provide detailed analysis, not just high-level overview.

Executive Summary:"""

# Clarification Prompts
CLARIFICATION_PROMPT = """The user's question is ambiguous or lacks context.

**User Question:**
{user_question}

**Missing Information:**
{missing_info}

**Available Options:**
{options}

Generate a friendly clarification question to help the user be more specific.

Clarification:"""

# Error Handling Prompts
ERROR_EXPLANATION_PROMPT = """An error occurred while processing the user's query.

**User Question:**
{user_question}

**Error Type:**
{error_type}

**Error Message:**
{error_message}

Generate a user-friendly explanation and suggest how to rephrase the question.

Response:"""

# Confidence Scoring Prompt
CONFIDENCE_SCORING_PROMPT = """Evaluate the confidence level of this SQL query for answering the user's question.

**User Question:**
{user_question}

**Generated SQL:**
{sql_query}

**Schema:**
{schema}

Rate confidence from 0.0 to 1.0 based on:
1. Query correctly interprets the question
2. All required data is accessible
3. Logic is sound
4. Results will be meaningful

Return only a number between 0.0 and 1.0.

Confidence Score:"""


def format_schema_for_prompt(schema_dict: dict) -> str:
    """Format schema dictionary for prompt inclusion"""
    schema_lines = ["Table: sales"]
    schema_lines.append("Columns:")
    for col_name, col_type in schema_dict.items():
        schema_lines.append(f"  - {col_name} ({col_type})")
    return "\n".join(schema_lines)


def format_conversation_history(history: list) -> str:
    """Format conversation history for prompt"""
    if not history:
        return "No previous conversation."

    lines = []
    for i, msg in enumerate(history[-5:], 1):  # Last 5 messages
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:200]  # Truncate long messages
        lines.append(f"{i}. {role}: {content}")

    return "\n".join(lines)


def format_query_results(results: list, max_rows: int = 10) -> str:
    """Format query results for prompt"""
    if not results:
        return "No results returned."

    # Show first few rows
    import json
    truncated = results[:max_rows]
    formatted = json.dumps(truncated, indent=2, default=str)

    if len(results) > max_rows:
        formatted += f"\n... ({len(results) - max_rows} more rows)"

    return formatted


__all__ = [
    'SQL_GENERATION_PROMPT',
    'VALIDATION_PROMPT',
    'INSIGHT_GENERATION_PROMPT',
    'SUMMARIZATION_PROMPT',
    'CLARIFICATION_PROMPT',
    'ERROR_EXPLANATION_PROMPT',
    'CONFIDENCE_SCORING_PROMPT',
    'format_schema_for_prompt',
    'format_conversation_history',
    'format_query_results',
]
