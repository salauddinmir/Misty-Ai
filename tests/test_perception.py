"""Tests for the multimodal perception module."""

import numpy as np

from brain.cognition import PerceptionPipeline
from brain.perception.audio import AudioEncoder
from brain.perception.gateway import MultimodalGateway
from brain.perception.image import ImageEncoder


class TestImageEncoder:
    """Image encoder produces stable 64-dim descriptors."""

    def test_array_input_shape(self) -> None:
        encoder = ImageEncoder()
        img = np.random.default_rng(42).integers(0, 256, (120, 160, 3), dtype=np.uint8)
        out = encoder.encode(img)
        assert out.shape == (64,)
        assert abs(float(np.linalg.norm(out)) - 1.0) < 1e-6

    def test_grayscale_promoted_to_rgb(self) -> None:
        encoder = ImageEncoder()
        gray = np.full((32, 32), 128, dtype=np.uint8)
        out = encoder.encode(gray)
        assert out.shape == (64,)

    def test_deterministic(self) -> None:
        encoder = ImageEncoder()
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        assert np.array_equal(encoder.encode(img), encoder.encode(img))

    def test_bright_vs_dark_differ(self) -> None:
        encoder = ImageEncoder()
        bright = np.full((64, 64, 3), 240, dtype=np.uint8)
        dark = np.full((64, 64, 3), 10, dtype=np.uint8)
        dist = float(np.linalg.norm(encoder.encode(bright) - encoder.encode(dark)))
        assert dist > 0.5

    def test_invalid_input_raises(self) -> None:
        encoder = ImageEncoder()
        import pytest

        with pytest.raises(TypeError):
            encoder.encode("not-image")


class TestAudioEncoder:
    """Audio encoder produces stable 64-dim descriptors."""

    def test_array_input_shape(self) -> None:
        rng = np.random.default_rng(1)
        samples = rng.standard_normal(8000)
        encoder = AudioEncoder()
        out = encoder.encode(samples)
        assert out.shape == (64,)
        assert abs(float(np.linalg.norm(out)) - 1.0) < 1e-6

    def test_sample_rate_tuple(self) -> None:
        samples = np.zeros(4000)
        vector = AudioEncoder().encode((samples, 22050))
        assert vector.shape == (64,)
        assert abs(float(np.linalg.norm(vector)) - 1.0) < 1e-6

    def test_tone_vs_silence_differ(self) -> None:
        t = np.linspace(0, 1.0, 16000)
        tone = np.sin(2 * np.pi * 440 * t)
        silence = np.zeros(16000)
        dist = float(np.linalg.norm(AudioEncoder().encode(tone) - AudioEncoder().encode(silence)))
        assert dist > 0.5

    def test_invalid_input_raises(self) -> None:
        import pytest

        with pytest.raises(TypeError):
            AudioEncoder().encode("not-audio")


class TestMultimodalGateway:
    """Gateway routes inputs to the right encoder."""

    def test_register_and_list(self) -> None:
        gw = MultimodalGateway()
        gw.register(ImageEncoder(), AudioEncoder())
        assert set(gw.modalities) == {"image", "audio"}

    def test_process_image(self) -> None:
        gw = MultimodalGateway()
        gw.register(ImageEncoder())
        img = np.zeros((32, 32, 3), dtype=np.uint8)
        vector, meta = gw.process_input("image", img)
        assert vector.shape == (64,)
        assert meta["modality"] == "image"
        assert meta["fallback"] is False

    def test_unknown_modality_fallback(self) -> None:
        gw = MultimodalGateway()
        gw.register(ImageEncoder())
        vector, meta = gw.process_input("smell", b"")
        assert vector.shape == (64,)
        assert meta["fallback"] is True
        assert meta["encoder"] is None

    def test_feature_size_lookup(self) -> None:
        gw = MultimodalGateway()
        gw.register(AudioEncoder())
        assert gw.feature_size("audio") == 64
        assert gw.feature_size("unknown") == 64


def test_bengali_question_receives_epistemic_attention() -> None:
    percept = PerceptionPipeline().perceive("তুমি কীভাবে অঙ্ক সমাধান করো?")

    assert percept.question_demand == 0.8
    assert percept.attention_weight > 0.4
    assert percept.event.event_type == "utterance"
    assert percept.event.reliability == 0.9


def test_urgent_input_receives_high_urgency() -> None:
    percept = PerceptionPipeline().perceive("জরুরি সাহায্য দরকার")

    assert percept.urgency == 0.9
    assert percept.attention_weight > 0.4


def test_sensor_percept_is_marked_less_reliable_than_text() -> None:
    percept = PerceptionPipeline().perceive("temperature=22", source="sensor")

    assert percept.event.event_type == "sensor_percept"
    assert percept.event.reliability == 0.75
    assert percept.event.source == "sensor"
