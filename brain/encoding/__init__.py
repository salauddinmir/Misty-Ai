"""
Spike Encoding Module.

Provides encoders and decoders for converting between external
representations (text, concepts) and neural spike patterns used
by the spiking neural network.
"""

from brain.encoding.concept_encoder import ConceptEncoder
from brain.encoding.decoder import Decoder
from brain.encoding.text_encoder import TextEncoder

__all__ = ["ConceptEncoder", "Decoder", "TextEncoder"]
