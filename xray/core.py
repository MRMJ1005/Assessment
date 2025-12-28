"""
X-Ray SDK Core - General-purpose decision tracking system
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class DecisionStep:
    """Represents a single step in a decision process"""
    step_id: str
    step_name: str
    timestamp: datetime
    inputs: Dict[str, Any] = field(default_factory=dict)
    candidates: List[Any] = field(default_factory=list)
    filters_applied: List[Dict[str, Any]] = field(default_factory=list)
    outcomes: Dict[str, Any] = field(default_factory=dict)
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class XRayContext:
    """
    Main context manager for tracking multi-step decision processes.
    This is the core of the X-Ray SDK.
    """
    
    def __init__(self, execution_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an X-Ray context for tracking a decision process.
        
        Args:
            execution_id: Optional unique identifier for this execution.
                         If not provided, a UUID will be generated.
            metadata: Optional metadata to attach to the execution.
        """
        self.execution_id = execution_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        self.steps: List[DecisionStep] = []
        self.created_at = datetime.now()
        self._current_step: Optional[DecisionStep] = None
    
    def start_step(
        self,
        step_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a new decision step.
        
        Args:
            step_name: Name/description of the step
            inputs: Input data for this step
            metadata: Additional metadata for this step
            
        Returns:
            step_id: Unique identifier for this step
        """
        step_id = str(uuid.uuid4())
        step = DecisionStep(
            step_id=step_id,
            step_name=step_name,
            timestamp=datetime.now(),
            inputs=inputs or {},
            metadata=metadata or {}
        )
        self.steps.append(step)
        self._current_step = step
        return step_id
    
    def add_candidates(self, candidates: List[Any], description: Optional[str] = None):
        """
        Record candidates considered in the current step.
        
        Args:
            candidates: List of candidate items
            description: Optional description of what these candidates represent
        """
        if not self._current_step:
            raise ValueError("No active step. Call start_step() first.")
        
        self._current_step.candidates = candidates
        if description:
            self._current_step.metadata['candidates_description'] = description
    
    def add_filter(
        self,
        filter_name: str,
        filter_config: Dict[str, Any],
        passed: List[Any],
        rejected: List[Any],
        reasoning: Optional[str] = None
    ):
        """
        Record a filter applied in the current step.
        
        Args:
            filter_name: Name of the filter
            filter_config: Configuration/parameters of the filter
            passed: Items that passed the filter
            rejected: Items that were rejected
            reasoning: Optional explanation of why items were filtered
        """
        if not self._current_step:
            raise ValueError("No active step. Call start_step() first.")
        
        filter_record = {
            'name': filter_name,
            'config': filter_config,
            'passed_count': len(passed),
            'rejected_count': len(rejected),
            'passed': passed,
            'rejected': rejected,
            'reasoning': reasoning
        }
        self._current_step.filters_applied.append(filter_record)
    
    def complete_step(
        self,
        outcomes: Optional[Dict[str, Any]] = None,
        reasoning: Optional[str] = None
    ):
        """
        Complete the current step.
        
        Args:
            outcomes: Final outcomes/results of this step
            reasoning: Optional explanation of the decision
        """
        if not self._current_step:
            raise ValueError("No active step. Call start_step() first.")
        
        if outcomes:
            self._current_step.outcomes = outcomes
        if reasoning:
            self._current_step.reasoning = reasoning
        
        self._current_step = None
    
    def get_trail(self) -> Dict[str, Any]:
        """
        Get the complete decision trail for this execution.
        
        Returns:
            Dictionary containing execution metadata and all steps
        """
        return {
            'execution_id': self.execution_id,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata,
            'steps': [step.to_dict() for step in self.steps],
            'total_steps': len(self.steps)
        }
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure current step is closed"""
        if self._current_step:
            self.complete_step()

