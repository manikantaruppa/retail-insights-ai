"""
Validation Agent: Validates SQL queries for safety and correctness
"""
import re
import json
from typing import Dict, Optional, List
from src.agents.base_agent import BaseAgent
from src.utils.prompts import VALIDATION_PROMPT, format_schema_for_prompt
from src.utils.logger import logger


class ValidationAgent(BaseAgent):
    """Validates SQL queries before execution"""

    # Dangerous SQL patterns
    FORBIDDEN_KEYWORDS = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT',
        'UPDATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
    ]

    # SQL injection patterns
    INJECTION_PATTERNS = [
        r';\s*DROP',
        r';\s*DELETE',
        r'--\s*$',
        r'/\*.*\*/',
        r'UNION.*SELECT',
        r'xp_cmdshell',
    ]

    def __init__(self):
        super().__init__("ValidationAgent")

    def validate_query(
        self,
        sql_query: str,
        schema: Dict[str, str]
    ) -> tuple[bool, List[str], Optional[str], str]:
        """
        Validate SQL query for safety and correctness

        Args:
            sql_query: SQL query to validate
            schema: Database schema

        Returns:
            tuple: (is_valid, issues, corrected_query, risk_level)
        """
        try:
            logger.info(f"Validating SQL query")

            issues = []

            # 1. Basic safety checks
            safety_issues = self._check_safety(sql_query)
            issues.extend(safety_issues)

            # 2. Schema validation
            schema_issues = self._check_schema(sql_query, schema)
            issues.extend(schema_issues)

            # 3. Syntax validation (basic)
            syntax_issues = self._check_syntax(sql_query)
            issues.extend(syntax_issues)

            # Determine risk level
            if any('CRITICAL' in issue for issue in issues):
                risk_level = 'high'
            elif any('WARNING' in issue for issue in issues):
                risk_level = 'medium'
            else:
                risk_level = 'low'

            # Query is valid if no critical issues
            is_valid = risk_level != 'high'

            if is_valid:
                logger.info(f"Query validation passed (risk: {risk_level})")
            else:
                logger.warning(f"Query validation failed: {issues}")

            # Try LLM validation for additional checks
            corrected_query = None
            if not is_valid:
                corrected_query = self._llm_validation(sql_query, schema, issues)

            return is_valid, issues, corrected_query, risk_level

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False, [f"Validation error: {str(e)}"], None, 'high'

    def _check_safety(self, sql_query: str) -> List[str]:
        """Check for dangerous SQL operations"""
        issues = []
        query_upper = sql_query.upper()

        # Check for forbidden keywords
        for keyword in self.FORBIDDEN_KEYWORDS:
            if re.search(rf'\b{keyword}\b', query_upper):
                issues.append(f"CRITICAL: Forbidden keyword '{keyword}' detected")

        # Check for SQL injection patterns
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, sql_query, re.IGNORECASE):
                issues.append(f"CRITICAL: Potential SQL injection pattern detected")

        # Must be a SELECT query
        if not query_upper.strip().startswith('SELECT'):
            issues.append(f"CRITICAL: Only SELECT queries are allowed")

        return issues

    def _check_schema(self, sql_query: str, schema: Dict[str, str]) -> List[str]:
        """Validate column names against schema"""
        issues = []

        # Extract column names from query (simplified)
        # Look for patterns like "column_name" in SELECT, WHERE, GROUP BY, ORDER BY
        column_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        potential_columns = re.findall(column_pattern, sql_query)

        # SQL keywords to ignore
        sql_keywords = {
            'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'HAVING',
            'LIMIT', 'AS', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
            'SUM', 'COUNT', 'AVG', 'MIN', 'MAX', 'DISTINCT', 'ASC', 'DESC',
            'CAST', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'NULL', 'IS',
            'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'USING'
        }

        invalid_columns = []
        for col in potential_columns:
            col_upper = col.upper()
            if col_upper not in sql_keywords and col not in schema:
                # Check if it's a table name (sales)
                if col_upper != 'SALES' and col != 'sales':
                    invalid_columns.append(col)

        if invalid_columns:
            issues.append(f"WARNING: Potentially invalid columns: {', '.join(set(invalid_columns[:5]))}")

        return issues

    def _check_syntax(self, sql_query: str) -> List[str]:
        """Basic syntax checks"""
        issues = []

        # Check for balanced parentheses
        if sql_query.count('(') != sql_query.count(')'):
            issues.append("WARNING: Unbalanced parentheses")

        # Check for basic SQL structure
        query_upper = sql_query.upper()
        if 'SELECT' in query_upper and 'FROM' not in query_upper:
            issues.append("WARNING: SELECT without FROM clause")

        return issues

    def _llm_validation(
        self,
        sql_query: str,
        schema: Dict[str, str],
        issues: List[str]
    ) -> Optional[str]:
        """Use LLM to validate and potentially correct query"""
        try:
            schema_str = format_schema_for_prompt(schema)

            prompt = VALIDATION_PROMPT.format(
                sql_query=sql_query,
                schema=schema_str
            )

            response, _ = self.generate_response(
                prompt=prompt,
                temperature=0.1
            )

            # Try to parse JSON response
            # Remove markdown if present
            response = response.strip()
            if response.startswith('```'):
                response = '\n'.join(response.split('\n')[1:-1])

            result = json.loads(response)

            if result.get('corrected_query'):
                logger.info("LLM suggested corrected query")
                return result['corrected_query']

        except Exception as e:
            logger.error(f"LLM validation failed: {e}")

        return None


__all__ = ['ValidationAgent']
