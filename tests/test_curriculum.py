import pytest

from brain.knowledge.curriculum import (
    CURRICULA,
    get_curriculum,
    list_curricula,
)


def test_all_phase_six_departments_are_registered():
    assert set(CURRICULA) == {"language", "mathematics", "physics", "literature"}
    assert [item.department for item in list_curricula()] == ["language", "literature", "mathematics", "physics"]


def test_every_curriculum_is_bilingual_and_has_a_benchmark():
    for curriculum in list_curricula():
        assert curriculum.languages == ("bn", "en")
        assert curriculum.prerequisites
        assert curriculum.units
        assert curriculum.package_ids
        assert curriculum.benchmark_ids
        assert curriculum.acceptance


def test_physics_depends_on_mathematics():
    assert "mathematics.core.v1" in get_curriculum("physics").prerequisites


def test_unknown_department_has_explicit_error():
    with pytest.raises(ValueError, match="unknown curriculum department"):
        get_curriculum("medicine")
