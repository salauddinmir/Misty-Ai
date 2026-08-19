"""
Phase 40: Per-user memory and personalization routes.

These endpoints let the frontend (and any authorized client) inspect
what Misty remembers about individual visitors, and ask her memory
questions in her own words:

- GET  /api/memory/users          — visitors Misty currently remembers
- GET  /api/memory/user           — full profile of one user
- GET  /api/memory/user/recall    — "What did I say about X?" personal recall

All endpoints are read-only and need no training key; they only expose
state the brain itself already maintains.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

router = APIRouter()


class UserSummaryResponse(BaseModel):
    """List of visitors Misty currently remembers."""

    user_count: int
    users: List[str]


class UserProfileResponse(BaseModel):
    """Full profile of one remembered user."""

    found: bool
    user_id: str = ""
    profile: Dict[str, Any] = {}


class PersonalRecallResponse(BaseModel):
    """Result of a personal-memory recall question."""

    user_id: str
    query: str
    recall: Dict[str, Any]


@router.get("/users", response_model=UserSummaryResponse)
def get_memory_users(request: Request) -> UserSummaryResponse:
    """List the visitor ids Misty currently has in her memory layer."""
    brain = request.app.state.brain
    user_memory = getattr(brain, "user_memory", None)
    if user_memory is None:
        raise HTTPException(status_code=503, detail="User memory layer not initialized.")
    return UserSummaryResponse(
        user_count=user_memory.user_count,
        users=user_memory.known_users(),
    )


@router.get("/user", response_model=UserProfileResponse)
def get_memory_user(
    request: Request,
    user_id: str = Query(..., description="Visitor id to look up (header or client-generated id)."),
) -> UserProfileResponse:
    """Full profile (facts + recent episodes) of one visitor."""
    brain = request.app.state.brain
    user_memory = getattr(brain, "user_memory", None)
    if user_memory is None:
        raise HTTPException(status_code=503, detail="User memory layer not initialized.")
    profile = user_memory.get_profile(user_id)
    if profile is None:
        return UserProfileResponse(found=False, user_id=user_id)
    return UserProfileResponse(found=True, user_id=user_id, profile=profile.to_dict())


@router.get("/user/recall", response_model=PersonalRecallResponse)
def get_memory_user_recall(
    request: Request,
    user_id: str = Query(..., description="Visitor id to recall for."),
    query: str = Query(..., min_length=1, max_length=500, description="Natural-language recall question."),
) -> PersonalRecallResponse:
    """Personal recall: which of this visitor's facts/episodes match the
    question's tokens (e.g. 'কাল কী বলেছিলাম', 'আমার প্রোফেশন কী')."""
    brain = request.app.state.brain
    user_memory = getattr(brain, "user_memory", None)
    if user_memory is None:
        raise HTTPException(status_code=503, detail="User memory layer not initialized.")
    recall = user_memory.personal_recall(user_id, query)
    return PersonalRecallResponse(user_id=user_id, query=query, recall=recall)
