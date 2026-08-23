"""Tests for Phase 57: NVIDIA Nemotron-3 Ultra LLM Integration."""

import os

import pytest

from brain.cognition.llm import LLMResponseGenerator, NVIDIAClient
from brain.core.brain import Brain


def test_nvidia_client_initialization():
    """Test that the NVIDIA client initializes correctly with env vars."""
    os.environ["NVIDIA_API_KEY"] = "test_key"
    client = NVIDIAClient()
    assert client.api_key == "test_key"
    assert client.is_available is True
    assert "nemotron-3-ultra" in client.model


def test_llm_response_generator_grounding():
    """Test that the response generator correctly formats grounding data."""
    brain = Brain()
    generator = LLMResponseGenerator(brain)

    context_data = {
        "recall_result": {
            "semantic_facts": [{"subject": "Misty", "predicate": "is_a", "obj": "Smart Artificial Brain"}]
        },
        "personal_recall": {"fact_matches": ["User name is Netvai"]},
    }

    grounding_str = generator._format_grounding_data(context_data)
    assert "Misty is_a Smart Artificial Brain" in grounding_str
    assert "User name is Netvai" in grounding_str


@pytest.mark.asyncio
async def test_brain_llm_status_in_state():
    """Test that brain state includes LLM status."""
    os.environ["NVIDIA_API_KEY"] = "test_key"
    brain = Brain()
    state = brain.get_state()

    assert "llm_status" in state
    assert state["llm_status"]["enabled"] is True
    assert "NVIDIA" in state["llm_status"]["provider"]


def test_should_search_heuristic():
    """Test the web search heuristic."""
    brain = Brain()
    generator = LLMResponseGenerator(brain)

    # Case 1: Low confidence act result
    context_low_conf = {"act_result": {"confidence": 0.2}}
    assert generator._should_search("who is X?", context_low_conf) is True

    # Case 2: High confidence act result
    context_high_conf = {"act_result": {"confidence": 0.9}}
    assert generator._should_search("hello", context_high_conf) is False

    # Case 3: Query intent with no facts
    context_no_facts = {
        "interpret_result": {"intent": "query_what"},
        "recall_result": {"semantic_facts": []},
        "act_result": {"confidence": 0.5},
    }
    assert generator._should_search("what is a pulsar?", context_no_facts) is True
