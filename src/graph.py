"""
LangGraph orchestration for multi-agent workflow
"""
from typing import Dict, List, Optional, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from src.agents.language_to_query_agent import LanguageToQueryAgent
from src.agents.validation_agent import ValidationAgent
from src.agents.extraction_agent import ExtractionAgent
from src.agents.insight_agent import InsightAgent
from src.agents.summarization_agent import SummarizationAgent
from src.utils.duckdb_manager import db_manager
from src.utils.metrics import metrics_tracker
from src.utils.logger import logger


class AgentState(TypedDict):
    """State passed between agents"""
    # Input
    mode: str  # 'summarization' or 'qa'
    user_question: Optional[str]
    conversation_history: List[Dict]
    column_mapping: Optional[Dict[str, str]]  # For dynamic column detection

    # Processing
    sql_query: Optional[str]
    confidence_score: Optional[float]
    validation_passed: bool
    validation_issues: List[str]

    # Results
    query_results: Optional[List[Dict]]
    rows_scanned: int

    # Output
    final_response: str
    error_message: Optional[str]

    # Metrics
    total_input_tokens: Annotated[int, operator.add]
    total_output_tokens: Annotated[int, operator.add]
    success: bool


class RetailInsightsGraph:
    """Orchestrates multi-agent workflow using LangGraph"""

    def __init__(self):
        # Initialize agents (summarization agent created dynamically with column mapping)
        self.language_agent = LanguageToQueryAgent()
        self.validation_agent = ValidationAgent()
        self.extraction_agent = ExtractionAgent()
        self.insight_agent = InsightAgent()

        # Build graph
        self.graph = self._build_graph()
        logger.info("Initialized RetailInsightsGraph")

    def _build_graph(self):
        """Build LangGraph workflow"""

        # Create state graph
        workflow = StateGraph(AgentState)

        # Add nodes (agents)
        workflow.add_node("route", self._route_mode)
        workflow.add_node("summarization", self._summarization_node)
        workflow.add_node("language_to_query", self._language_to_query_node)
        workflow.add_node("validation", self._validation_node)
        workflow.add_node("extraction", self._extraction_node)
        workflow.add_node("insight", self._insight_node)
        workflow.add_node("error_handler", self._error_handler_node)

        # Define edges (workflow)
        workflow.set_entry_point("route")

        # Route based on mode
        workflow.add_conditional_edges(
            "route",
            lambda state: state["mode"],
            {
                "summarization": "summarization",
                "qa": "language_to_query"
            }
        )

        # Summarization path
        workflow.add_edge("summarization", END)

        # Q&A path
        workflow.add_edge("language_to_query", "validation")

        # Validation conditional edge
        workflow.add_conditional_edges(
            "validation",
            lambda state: "pass" if state["validation_passed"] else "fail",
            {
                "pass": "extraction",
                "fail": "error_handler"
            }
        )

        workflow.add_conditional_edges(
            "extraction",
            lambda state: "success" if state.get("success", False) else "error",
            {
                "success": "insight",
                "error": "error_handler"
            }
        )

        workflow.add_edge("insight", END)
        workflow.add_edge("error_handler", END)

        return workflow.compile()

    def _route_mode(self, state: AgentState) -> AgentState:
        """Route to correct mode"""
        logger.info(f"Routing to mode: {state['mode']}")
        return state

    def _summarization_node(self, state: AgentState) -> AgentState:
        """Summarization agent node"""
        try:
            logger.info("Executing summarization mode")
            metrics_tracker.mark_stage('summarization')

            # Create summarization agent with column mapping
            column_mapping = state.get("column_mapping")
            if not column_mapping:
                raise ValueError("Column mapping required for summarization mode")

            summarization_agent = SummarizationAgent(column_mapping=column_mapping)
            summary, token_usage = summarization_agent.generate_summary()

            state["final_response"] = summary
            state["success"] = True
            state["total_input_tokens"] = token_usage["input_tokens"]
            state["total_output_tokens"] = token_usage["output_tokens"]

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            state["final_response"] = f"Failed to generate summary: {str(e)}"
            state["success"] = False
            state["error_message"] = str(e)

        return state

    def _language_to_query_node(self, state: AgentState) -> AgentState:
        """Language-to-Query agent node"""
        try:
            logger.info("Converting question to SQL")
            metrics_tracker.mark_stage('sql_generation')

            schema = db_manager.schema or db_manager.get_schema()

            sql_query, confidence, token_usage = self.language_agent.generate_sql(
                user_question=state["user_question"],
                schema=schema,
                conversation_history=state.get("conversation_history", [])
            )

            state["sql_query"] = sql_query
            state["confidence_score"] = confidence
            state["total_input_tokens"] = token_usage["input_tokens"]
            state["total_output_tokens"] = token_usage["output_tokens"]

        except Exception as e:
            logger.error(f"Language-to-Query failed: {e}")
            state["sql_query"] = None
            state["confidence_score"] = 0.0
            state["error_message"] = str(e)

        return state

    def _validation_node(self, state: AgentState) -> AgentState:
        """Validation agent node"""
        try:
            logger.info("Validating SQL query")

            schema = db_manager.schema or db_manager.get_schema()

            is_valid, issues, corrected_query, risk_level = self.validation_agent.validate_query(
                sql_query=state["sql_query"],
                schema=schema
            )

            state["validation_passed"] = is_valid
            state["validation_issues"] = issues

            # Use corrected query if validation failed but correction available
            if not is_valid and corrected_query:
                logger.info("Using corrected SQL query")
                state["sql_query"] = corrected_query
                state["validation_passed"] = True

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            state["validation_passed"] = False
            state["validation_issues"] = [str(e)]

        return state

    def _extraction_node(self, state: AgentState) -> AgentState:
        """Extraction agent node"""
        try:
            logger.info("Executing SQL query")
            metrics_tracker.mark_stage('sql_execution')

            success, results, error_msg, rows_scanned = self.extraction_agent.execute_query(
                sql_query=state["sql_query"]
            )

            state["success"] = success
            state["query_results"] = results
            state["rows_scanned"] = rows_scanned

            if not success:
                state["error_message"] = error_msg

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            state["success"] = False
            state["error_message"] = str(e)

        return state

    def _insight_node(self, state: AgentState) -> AgentState:
        """Insight agent node"""
        try:
            logger.info("Generating insight")
            metrics_tracker.mark_stage('insight_generation')

            insight, token_usage = self.insight_agent.generate_insight(
                user_question=state["user_question"],
                sql_query=state["sql_query"],
                query_results=state["query_results"]
            )

            state["final_response"] = insight
            state["total_input_tokens"] = state.get("total_input_tokens", 0) + token_usage["input_tokens"]
            state["total_output_tokens"] = state.get("total_output_tokens", 0) + token_usage["output_tokens"]

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            state["final_response"] = f"Query executed successfully but failed to generate insight: {str(e)}"

        return state

    def _error_handler_node(self, state: AgentState) -> AgentState:
        """Error handler node"""
        try:
            logger.info("Handling error")

            if state.get("validation_issues"):
                error_type = "Validation Error"
                error_msg = "; ".join(state["validation_issues"])
            else:
                error_type = "Execution Error"
                error_msg = state.get("error_message", "Unknown error")

            explanation, token_usage = self.insight_agent.generate_error_explanation(
                user_question=state.get("user_question", ""),
                error_type=error_type,
                error_message=error_msg
            )

            state["final_response"] = explanation
            state["success"] = False
            state["total_input_tokens"] = state.get("total_input_tokens", 0) + token_usage["input_tokens"]
            state["total_output_tokens"] = state.get("total_output_tokens", 0) + token_usage["output_tokens"]

        except Exception as e:
            logger.error(f"Error handler failed: {e}")
            state["final_response"] = "An error occurred while processing your request. Please try again."

        return state

    def process_query(
        self,
        mode: str,
        user_question: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Process user query through agent workflow

        Args:
            mode: 'summarization' or 'qa'
            user_question: User's question (for Q&A mode)
            conversation_history: Previous conversation context
            column_mapping: Column mapping for dynamic summarization

        Returns:
            Dictionary with response and metadata
        """
        try:
            # Start metrics tracking
            metrics_tracker.start_query()

            # Initialize state
            initial_state: AgentState = {
                "mode": mode,
                "user_question": user_question,
                "conversation_history": conversation_history or [],
                "column_mapping": column_mapping,
                "sql_query": None,
                "confidence_score": None,
                "validation_passed": False,
                "validation_issues": [],
                "query_results": None,
                "rows_scanned": 0,
                "final_response": "",
                "error_message": None,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "success": False
            }

            # Execute workflow
            logger.info(f"Starting workflow: mode={mode}")
            final_state = self.graph.invoke(initial_state)

            # Record metrics
            metrics_tracker.end_query(
                query_type=mode,
                user_query=user_question or "summarization",
                sql_query=final_state.get("sql_query"),
                input_tokens=final_state.get("total_input_tokens", 0),
                output_tokens=final_state.get("total_output_tokens", 0),
                success=final_state.get("success", False),
                error_message=final_state.get("error_message"),
                confidence_score=final_state.get("confidence_score"),
                rows_scanned=final_state.get("rows_scanned", 0)
            )

            return {
                "response": final_state["final_response"],
                "sql_query": final_state.get("sql_query"),
                "confidence_score": final_state.get("confidence_score"),
                "success": final_state.get("success", False),
                "error_message": final_state.get("error_message"),
                "rows_scanned": final_state.get("rows_scanned", 0),
                "token_usage": {
                    "input_tokens": final_state.get("total_input_tokens", 0),
                    "output_tokens": final_state.get("total_output_tokens", 0),
                    "total_tokens": final_state.get("total_input_tokens", 0) + final_state.get("total_output_tokens", 0)
                }
            }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "response": f"System error: {str(e)}",
                "sql_query": None,
                "confidence_score": 0.0,
                "success": False,
                "error_message": str(e),
                "rows_scanned": 0,
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            }


# Global graph instance
insights_graph = RetailInsightsGraph()

__all__ = ['RetailInsightsGraph', 'insights_graph']
