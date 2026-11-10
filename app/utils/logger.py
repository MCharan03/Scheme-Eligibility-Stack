import logging
from typing import List, Dict, Any
from app.models.schemas import ExecutionTraceStep

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
app_logger = logging.getLogger("SchemeNavigator")

class ExecutionTracer:
    """Collects safe, high-level execution steps for transparent evaluation."""
    def __init__(self):
        self.trace: List[ExecutionTraceStep] = []

    def record_step(self, agent: str, action: str, summary: str, details: Dict[str, Any] = None):
        step = ExecutionTraceStep(
            agent=agent,
            action=action,
            summary=summary,
            details=details or {}
        )
        self.trace.append(step)
        app_logger.info(f"[{agent}] {action}: {summary}")

    def get_trace(self) -> List[ExecutionTraceStep]:
        return list(self.trace)

    def clear(self):
        self.trace.clear()
