from brain.knowledge.registry import (
    PackageRegistry,
    PackageValidationError,
    SourceRef,
    TrainingPackageV2,
    validate_package,
)


def make_package(**overrides):
    values = {
        "package_id": "math.algebra.v1",
        "department": "mathematics",
        "version": "1.0.0",
        "languages": ["bn", "en"],
        "license": "CC-BY-4.0",
        "source": SourceRef(
            title="Open source mathematics",
            url="https://example.org/math",
            retrieved_at="2026-08-18T00:00:00Z",
            content_hash="sha256:abc123",
        ),
        "facts": [
            {
                "subject": "x",
                "predicate": "is_a",
                "obj": "variable",
                "source_ref": "https://example.org/math",
                "confidence": 0.95,
            }
        ],
    }
    values.update(overrides)
    return TrainingPackageV2(**values)


def test_valid_package_passes_validation_and_serializes_source():
    package = validate_package(make_package())
    assert package.to_dict()["source"]["content_hash"] == "sha256:abc123"


def test_package_requires_provenance_for_facts():
    package = make_package(facts=[{"subject": "x", "predicate": "is_a", "obj": "variable"}])
    try:
        validate_package(package)
    except PackageValidationError as exc:
        assert "source_ref" in str(exc)
    else:
        raise AssertionError("package without provenance should be rejected")


def test_package_rejects_duplicate_facts():
    fact = {
        "subject": "x",
        "predicate": "is_a",
        "obj": "variable",
        "source_ref": "https://example.org/math",
    }
    package = make_package(facts=[fact, fact.copy()])
    try:
        validate_package(package)
    except PackageValidationError as exc:
        assert "duplicate facts" in str(exc)
    else:
        raise AssertionError("duplicate fact should be rejected")


def test_registry_rejects_same_package_version_but_allows_new_version():
    registry = PackageRegistry([make_package()])
    try:
        registry.register(make_package())
    except PackageValidationError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("same package version should be rejected")

    registry.register(make_package(version="1.1.0"))
    assert len(registry.list("mathematics")) == 2


def test_only_bengali_and_english_are_allowed():
    package = make_package(languages=["bn", "fr"])
    try:
        validate_package(package)
    except PackageValidationError as exc:
        assert "languages" in str(exc)
    else:
        raise AssertionError("unsupported language should be rejected")
