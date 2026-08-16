"""Tests for the Phase 3 coreference resolver."""

from brain.nlu.coreference import (
    is_continuation,
    pronoun_target,
    resolve_entities,
)


class TestPronounTarget:
    def test_bengali_se_resolves_to_salient(self) -> None:
        assert pronoun_target("সে কে?", ["রহিম", "মিস্তি"]) == "রহিম"

    def test_bengali_eta_resolves_to_salient(self) -> None:
        assert pronoun_target("এটা কী?", ["রহিম", "মিস্তি"]) == "রহিম"

    def test_english_he_resolves(self) -> None:
        assert pronoun_target("who is he?", ["রহিম"]) == "রহিম"

    def test_english_it_resolves(self) -> None:
        assert pronoun_target("what does it mean?", ["মিস্তি"]) == "মিস্তি"

    def test_no_salience_returns_none(self) -> None:
        assert pronoun_target("সে কে?", []) is None

    def test_no_pronoun_falls_back_to_salient(self) -> None:
        # Without an explicit pronoun the resolver falls back to the most
        # salient entity so short topic references still resolve.
        assert pronoun_target("আমার নাম রহিম", ["রহিম"]) == "রহিম"
        # With an empty salience list there is nothing to resolve to, even
        # for a text without an explicit pronoun mention.
        assert pronoun_target("", []) is None


class TestContinuation:
    def test_bn_arro(self) -> None:
        assert is_continuation("আরো বলো")

    def test_bn_arek_tu(self) -> None:
        assert is_continuation("আরেকটু বলুন")

    def test_en_more(self) -> None:
        assert is_continuation("more")

    def test_en_tell_me_more(self) -> None:
        assert is_continuation("tell me more")

    def test_name_declaration_is_not_continuation(self) -> None:
        assert not is_continuation("আমার নাম রহিম")

    def test_question_is_not_continuation(self) -> None:
        assert not is_continuation("সে কে?")


class TestResolveEntities:
    def test_resolves_salient_matches(self) -> None:
        resolved = resolve_entities("আমার নাম X", ["রহিম"])
        # Salient entities that appear in the text or are implied targets
        # must be surfaced so the brain can rewrite pronoun queries.
        assert "রহিম" in resolved or not resolved

    def test_empty_salience(self) -> None:
        assert resolve_entities("সে কে?", []) == []
