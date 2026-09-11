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


def test_llm_messages_use_bounded_dialogue_snapshot() -> None:
    brain = Brain()
    brain.dialogue_context.add_turn("আমি রাহুল", role="user")
    brain.dialogue_context.add_turn("স্বাগতম রাহুল", role="brain")
    generator = LLMResponseGenerator(brain)

    messages = generator._build_messages("আজ কেমন আছ?", {})

    assert messages[-3]["role"] == "user"
    assert messages[-3]["content"] == "আমি রাহুল"
    assert messages[-2]["role"] == "assistant"
    assert messages[-2]["content"] == "স্বাগতম রাহুল"
    assert messages[-1] == {"role": "user", "content": "আজ কেমন আছ?"}


@pytest.mark.asyncio
async def test_nvidia_client_rejects_malformed_success_payload(monkeypatch):
    class FakeResponse:
        status_code = 200
        text = "{}"

        @staticmethod
        def json():
            return {"choices": []}

    class FakeClient:
        def __init__(self, **kwargs):
            self.calls = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            self.calls += 1
            return FakeResponse()

    monkeypatch.setenv("NVIDIA_API_KEY", "test_key")
    monkeypatch.setenv("MISTY_LLM_MAX_RETRIES", "0")
    monkeypatch.setattr("brain.cognition.llm.httpx.AsyncClient", FakeClient)

    result = await NVIDIAClient().chat_completion([{"role": "user", "content": "hello"}])
    assert result["success"] is False
    assert result["error"] == "INVALID_PROVIDER_RESPONSE"


def test_nvidia_client_reads_runtime_limits(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "test_key")
    monkeypatch.setenv("MISTY_LLM_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("MISTY_LLM_MAX_RETRIES", "3")
    client = NVIDIAClient()
    assert client.timeout == 12.0
    assert client.max_retries == 3
