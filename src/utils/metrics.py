"""
Metrics tracking for cost, latency, and performance monitoring
"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from src.config import Config
from src.utils.logger import logger


@dataclass
class QueryMetrics:
    """Metrics for a single query execution"""
    timestamp: str
    query_type: str  # 'summarization' or 'qa'
    user_query: str
    sql_query: Optional[str]

    # Performance metrics
    total_latency_ms: float
    sql_generation_time_ms: float
    sql_execution_time_ms: float
    insight_generation_time_ms: float

    # Cost metrics
    input_tokens: int
    output_tokens: int
    total_cost: float

    # Quality metrics
    success: bool
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None
    rows_scanned: Optional[int] = None


@dataclass
class SessionMetrics:
    """Aggregated metrics for a session"""
    session_id: str
    start_time: str
    queries: List[QueryMetrics] = field(default_factory=list)

    def add_query(self, metrics: QueryMetrics):
        """Add query metrics to session"""
        self.queries.append(metrics)

    def get_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.queries:
            return {
                "total_queries": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "total_cost": 0.0,
            }

        successful = [q for q in self.queries if q.success]

        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "total_queries": len(self.queries),
            "successful_queries": len(successful),
            "failed_queries": len(self.queries) - len(successful),
            "success_rate": len(successful) / len(self.queries) * 100,
            "avg_latency_ms": sum(q.total_latency_ms for q in self.queries) / len(self.queries),
            "total_latency_ms": sum(q.total_latency_ms for q in self.queries),
            "avg_sql_execution_ms": sum(q.sql_execution_time_ms for q in self.queries) / len(self.queries),
            "total_tokens": sum(q.input_tokens + q.output_tokens for q in self.queries),
            "total_cost": sum(q.total_cost for q in self.queries),
            "avg_confidence": sum(q.confidence_score or 0 for q in successful) / len(successful) if successful else 0,
        }

    def export_to_json(self, filepath: Path):
        """Export metrics to JSON file"""
        data = {
            "summary": self.get_summary(),
            "queries": [
                {
                    "timestamp": q.timestamp,
                    "query_type": q.query_type,
                    "user_query": q.user_query,
                    "sql_query": q.sql_query,
                    "latency_ms": q.total_latency_ms,
                    "cost": q.total_cost,
                    "success": q.success,
                    "confidence": q.confidence_score,
                }
                for q in self.queries
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")


class MetricsTracker:
    """Global metrics tracker"""

    def __init__(self):
        self.current_session: Optional[SessionMetrics] = None
        self._query_start_time: Optional[float] = None
        self._stage_times: Dict[str, float] = {}

    def start_session(self, session_id: str):
        """Start a new metrics session"""
        self.current_session = SessionMetrics(
            session_id=session_id,
            start_time=datetime.now().isoformat()
        )
        logger.info(f"Started metrics tracking for session: {session_id}")

    def start_query(self):
        """Mark the start of a query"""
        self._query_start_time = time.time()
        self._stage_times = {}

    def mark_stage(self, stage_name: str):
        """Mark completion of a stage"""
        if self._query_start_time:
            self._stage_times[stage_name] = time.time()

    def end_query(
        self,
        query_type: str,
        user_query: str,
        sql_query: Optional[str],
        input_tokens: int,
        output_tokens: int,
        success: bool,
        error_message: Optional[str] = None,
        confidence_score: Optional[float] = None,
        rows_scanned: Optional[int] = None,
    ):
        """Record completed query metrics"""
        if not self._query_start_time or not self.current_session:
            logger.warning("Attempted to end query without starting session/query")
            return

        end_time = time.time()
        total_latency = (end_time - self._query_start_time) * 1000  # Convert to ms

        # Calculate stage times
        sql_gen_time = (self._stage_times.get('sql_generation', self._query_start_time) - self._query_start_time) * 1000
        sql_exec_time = (self._stage_times.get('sql_execution', self._query_start_time) - self._stage_times.get('sql_generation', self._query_start_time)) * 1000
        insight_time = (end_time - self._stage_times.get('insight_generation', end_time)) * 1000

        # Calculate cost
        total_cost = (
            (input_tokens / 1_000_000) * Config.GEMINI_INPUT_COST +
            (output_tokens / 1_000_000) * Config.GEMINI_OUTPUT_COST
        )

        metrics = QueryMetrics(
            timestamp=datetime.now().isoformat(),
            query_type=query_type,
            user_query=user_query,
            sql_query=sql_query,
            total_latency_ms=total_latency,
            sql_generation_time_ms=sql_gen_time,
            sql_execution_time_ms=sql_exec_time,
            insight_generation_time_ms=insight_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=total_cost,
            success=success,
            error_message=error_message,
            confidence_score=confidence_score,
            rows_scanned=rows_scanned,
        )

        self.current_session.add_query(metrics)

        logger.info(
            f"Query completed - Type: {query_type}, "
            f"Latency: {total_latency:.0f}ms, "
            f"Cost: ${total_cost:.4f}, "
            f"Success: {success}"
        )

    def get_session_summary(self) -> Dict:
        """Get current session summary"""
        if self.current_session:
            return self.current_session.get_summary()
        return {}

    def export_session(self, output_dir: Optional[Path] = None):
        """Export current session metrics"""
        if not self.current_session:
            logger.warning("No active session to export")
            return

        if output_dir is None:
            output_dir = Config.LOGS_DIR

        filepath = output_dir / f"metrics_{self.current_session.session_id}.json"
        self.current_session.export_to_json(filepath)


# Global metrics tracker instance
metrics_tracker = MetricsTracker()

__all__ = ['metrics_tracker', 'MetricsTracker', 'QueryMetrics', 'SessionMetrics']
