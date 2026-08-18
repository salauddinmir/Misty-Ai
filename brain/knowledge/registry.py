"""Versioned, provenance-aware training package registry for MISTY.

The registry is deliberately deterministic and dependency-free. It validates
structured knowledge before a package is allowed into the cognitive graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Sequence
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceRef:
    title: str
    url: str
    retrieved_at: str
    content_hash: str


@dataclass
class TrainingPackageV2:
    package_id: str
    department: str
    version: str
    languages: List[str]
    license: str
    source: SourceRef
    prerequisites: List[str] = field(default_factory=list)
    concepts: List[Dict[str, Any]] = field(default_factory=list)
    relations: List[Dict[str, Any]] = field(default_factory=list)
    facts: List[Dict[str, Any]] = field(default_factory=list)
    rules: List[Dict[str, Any]] = field(default_factory=list)
    formulas: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    tests: List[Dict[str, Any]] = field(default_factory=list)
    confidence_policy: Dict[str, Any] = field(default_factory=lambda: {"default": 0.8, "requires_source": True})

    def to_dict(self) -> Dict[str, Any]:
        result = dict(self.__dict__)
        result["source"] = dict(self.source.__dict__)
        return result


class PackageValidationError(ValueError):
    """Raised when a training package cannot safely enter the knowledge graph."""


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PackageValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


def _validate_source(source: SourceRef) -> None:
    _require_text(source.title, "source.title")
    url = _require_text(source.url, "source.url")
    if urlparse(url).scheme not in {"http", "https"}:
        raise PackageValidationError("source.url must use http or https")
    _require_text(source.retrieved_at, "source.retrieved_at")
    try:
        datetime.fromisoformat(source.retrieved_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PackageValidationError("source.retrieved_at must be ISO-8601") from exc
    content_hash = _require_text(source.content_hash, "source.content_hash")
    if not content_hash.startswith("sha256:"):
        raise PackageValidationError("source.content_hash must start with sha256:")


def _validate_records(records: Sequence[Mapping[str, Any]], name: str) -> None:
    seen: set[tuple[str, ...]] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise PackageValidationError(f"{name}[{index}] must be an object")
        key_fields = {
            "concepts": ("name",),
            "relations": ("source", "target", "type"),
            "facts": ("subject", "predicate", "obj"),
            "rules": ("when", "then"),
            "formulas": ("name", "expression"),
            "examples": ("input", "output"),
            "tests": ("id", "input", "expected_output"),
        }.get(name, ())
        key: tuple[str, ...] = tuple(
            _require_text(record.get(field), f"{name}[{index}].{field}") for field in key_fields
        )
        if key and key in seen:
            raise PackageValidationError(f"duplicate {name} record: {key}")
        if key:
            seen.add(key)
        if "confidence" in record:
            confidence = record["confidence"]
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                raise PackageValidationError(f"{name}[{index}].confidence must be between 0 and 1")
        if name in {"facts", "rules", "formulas", "examples", "tests"}:
            source_ref = record.get("source_ref")
            if not source_ref:
                raise PackageValidationError(f"{name}[{index}] requires source_ref")


def validate_package(package: TrainingPackageV2) -> TrainingPackageV2:
    """Validate package identity, provenance, records, and confidence policy."""
    _require_text(package.package_id, "package_id")
    _require_text(package.department, "department")
    _require_text(package.version, "version")
    if not package.languages or any(language not in {"bn", "en"} for language in package.languages):
        raise PackageValidationError("languages must contain only bn and/or en")
    _require_text(package.license, "license")
    _validate_source(package.source)
    for prerequisite in package.prerequisites:
        _require_text(prerequisite, "prerequisite")
    for name in ("concepts", "relations", "facts", "rules", "formulas", "examples", "tests"):
        _validate_records(getattr(package, name), name)
    default_confidence = package.confidence_policy.get("default")
    if not isinstance(default_confidence, (int, float)) or not 0 <= default_confidence <= 1:
        raise PackageValidationError("confidence_policy.default must be between 0 and 1")
    return package


class PackageRegistry:
    """In-memory registry used by loaders and tests; persistence is external."""

    def __init__(self, packages: Iterable[TrainingPackageV2] = ()) -> None:
        self._packages: Dict[tuple[str, str], TrainingPackageV2] = {}
        for package in packages:
            self.register(package)

    def register(self, package: TrainingPackageV2) -> TrainingPackageV2:
        validate_package(package)
        key = (package.package_id, package.version)
        if key in self._packages:
            raise PackageValidationError(f"package version already registered: {package.package_id}@{package.version}")
        self._packages[key] = package
        return package

    def get(self, package_id: str) -> TrainingPackageV2 | None:
        versions = [package for (identifier, _), package in self._packages.items() if identifier == package_id]
        return sorted(versions, key=lambda package: package.version)[-1] if versions else None

    def list(self, department: str | None = None) -> List[TrainingPackageV2]:
        packages = list(self._packages.values())
        if department is not None:
            packages = [package for package in packages if package.department == department]
        return sorted(packages, key=lambda package: (package.package_id, package.version))
