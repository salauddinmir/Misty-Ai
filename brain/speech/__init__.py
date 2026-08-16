"""Offline speech pipeline for the Misty brain.

Provides dependency-free text-to-speech (espeak) and optional
offline speech-to-text (Whisper, imported lazily). Neither engine
ever calls any cloud API.
"""

from brain.speech.stt import OfflineSTT
from brain.speech.tts import OfflineTTS

__all__ = ["OfflineSTT", "OfflineTTS"]
