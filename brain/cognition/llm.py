"""NVIDIA NIM (Nemotron-3 Ultra) LLM Integration for MISTY."""

import logging
import os
import time
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class NVIDIAClient:
    """Client for NVIDIA NIM APIs, specifically Nemotron-3 Ultra."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        model: str = "nvidia/nemotron-3-ultra-550b-a55b",
    ):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        self.base_url = base_url
        self.model = model
        self.timeout = 60.0

    @property
    def is_available(self) -> bool:
        """Check if the client is configured with an API key."""
        return bool(self.api_key)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 1.0,
    ) -> Dict[str, Any]:
        """Call the NVIDIA NIM Chat Completion API."""
        if not self.is_available:
            raise ValueError("NVIDIA_API_KEY is not set.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                start_time = time.monotonic()
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                elapsed = time.monotonic() - start_time

                if response.status_code != 200:
                    logger.error(f"NVIDIA API Error {response.status_code}: {response.text}")
                    return {"error": f"API Error {response.status_code}", "detail": response.text, "success": False}

                data = response.json()
                return {
                    "response": data["choices"][0]["message"]["content"],
                    "usage": data.get("usage", {}),
                    "elapsed_sec": elapsed,
                    "success": True,
                }
            except Exception as e:
                logger.exception("Failed to call NVIDIA NIM API")
                return {"error": str(e), "success": False}


class LLMResponseGenerator:
    """Orchestrates LLM-driven response generation with cognitive grounding."""

    def __init__(self, brain: Any):
        self.brain = brain
        self.client = NVIDIAClient()
        # Reuse existing WebSearchLearner for search capabilities
        self.web_learner = brain.web_learner

    async def generate_response(
        self, text_input: str, context_data: Dict[str, Any], system_prompt: str | None = None
    ) -> Dict[str, Any]:
        """Generate a grounded response using Nemotron-3 Ultra."""
        if not self.client.is_available:
            return {"success": False, "error": "LLM_NOT_CONFIGURED"}

        # Phase 4: Optional Web Search for better answers
        web_search_context = ""
        if self._should_search(text_input, context_data):
            web_search_context = await self._perform_web_search(text_input)

        # Construct the grounded prompt
        messages = self._build_messages(text_input, context_data, system_prompt, web_search_context)

        result = await self.client.chat_completion(messages)
        return result

    def _should_search(self, text_input: str, context_data: Dict[str, Any]) -> bool:
        """Heuristic to decide if a web search is needed."""
        # Search if the deterministic act phase has low confidence or is unknown
        act_result = context_data.get("act_result", {})
        if act_result.get("confidence", 0.0) < 0.4:
            return True

        # Search if intent is a query and no facts were recalled
        interpret = context_data.get("interpret_result", {})
        recall = context_data.get("recall_result", {})
        if interpret.get("intent") in ["query_who", "query_what"] and not recall.get("semantic_facts"):
            return True

        return False

    async def _perform_web_search(self, text_input: str) -> str:
        """Use the existing WebSearchLearner to gather external context."""
        try:
            # Extract target from input
            target = text_input
            if "?" in text_input:
                target = text_input.split("?")[0].strip()

            snippets = await self.web_learner.search(target, max_results=3)
            if not snippets:
                return ""

            context = "\nEXTERNAL WEB SEARCH RESULTS:\n"
            for s in snippets:
                context += f"- {s['snippet']} (Source: {s['url']})\n"
            return context
        except Exception as e:
            logger.error(f"Web search for LLM failed: {e}")
            return ""

    def _build_messages(
        self,
        text_input: str,
        context_data: Dict[str, Any],
        system_prompt: str | None = None,
        web_search_context: str = "",
    ) -> List[Dict[str, str]]:
        """Construct the message history and grounding context for the LLM."""

        # Identity and core personality
        identity = (
            "You are MISTY, a Smart Artificial Brain created by Pixline Incorporate. "
            "Your founder is Salauddin Mir, also known as Netvai. "
            "You are India's first Smart AI Brain. "
            "You speak both Bengali and English fluently. "
            "You are helpful, empathetic, and scientifically accurate."
        )

        # Grounding: Extract facts and recent memories
        grounding_context = self._format_grounding_data(context_data)

        final_system_prompt = system_prompt or (
            f"{identity}\n\n"
            f"CURRENT CONTEXT & KNOWLEDGE:\n{grounding_context}\n"
            f"{web_search_context}\n"
            "Use the provided knowledge to answer the user. If the knowledge is insufficient, "
            "you may use your internal reasoning, but prioritize the provided facts about MISTY's "
            "identity and specific domain knowledge."
        )

        messages = [{"role": "system", "content": final_system_prompt}]

        # Add bounded dialogue history if available. The internal context uses
        # ``brain`` for assistant turns; Nemotron expects ``assistant``.
        history = self.brain.dialogue_context.get_context_snapshot(max_turns=5)
        messages.extend(
            {
                "role": "assistant" if turn["role"] == "brain" else "user",
                "content": turn["text"],
            }
            for turn in history
        )

        # Add current input
        messages.append({"role": "user", "content": text_input})

        return messages

    def _format_grounding_data(self, context_data: Dict[str, Any]) -> str:
        """Format semantic facts and episodic memories for the prompt."""
        lines = []

        # Semantic facts from RECALL phase
        facts = context_data.get("recall_result", {}).get("semantic_facts", [])
        if facts:
            lines.append("Relevant Facts:")
            lines.extend(f"- {f.get('subject')} {f.get('predicate')} {f.get('obj')}" for f in facts[:10])

        # Personal recall
        personal = context_data.get("personal_recall", {})
        if personal.get("fact_matches"):
            lines.append("\nPersonal Knowledge about the User:")
            lines.extend(f"- {f}" for f in personal["fact_matches"][:5])

        # Active concepts
        concepts = context_data.get("associate_result", {}).get("activation_map", {})
        if concepts:
            active_list = ", ".join(list(concepts.keys())[:5])
            lines.append(f"\nActive Concepts: {active_list}")

        return "\n".join(lines) if lines else "No specific grounding data available."
