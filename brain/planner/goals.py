"""
Goal Class.

Represents a goal that the brain is trying to achieve.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from enum import Enum
import time as time_module
import uuid


class GoalStatus(str, Enum):
    """Possible states of a goal."""
    PENDING = "pending"
    ACTIVE = "active"
    ACHIEVED = "achieved"
    FAILED = "failed"
    ABANDONED = "abandoned"


@dataclass
class Goal:
    """A goal the brain is pursuing."""

    description: str
    goal_type: str = "respond"
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    priority: float = 0.5
    status: GoalStatus = GoalStatus.PENDING
    created_at: float = field(default_factory=time_module.time)
    sub_goals: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def activate(self) -> None:
        """Mark this goal as active."""
        self.status = GoalStatus.ACTIVE

    def achieve(self) -> None:
        """Mark this goal as achieved."""
        self.status = GoalStatus.ACHIEVED

    def fail(self, reason: str = "") -> None:
        """Mark this goal as failed."""
        self.status = GoalStatus.FAILED
        self.context["failure_reason"] = reason

    def abandon(self) -> None:
        """Abandon this goal."""
        self.status = GoalStatus.ABANDONED

    @property
    def is_terminal(self) -> bool:
        """Whether this goal is in a terminal state."""
        return self.status in (GoalStatus.ACHIEVED, GoalStatus.FAILED, GoalStatus.ABANDONED)

    def __repr__(self) -> str:
        return (
            f"Goal(desc='{self.description[:30]}...', "
            f"type={self.goal_type}, status={self.status.value})"
        )
