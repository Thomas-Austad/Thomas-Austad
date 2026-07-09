import pytest

from tests.agent_regression_cases import MatchRegressionCase, match_regression_cases


def _assert_match_invariants(case: MatchRegressionCase) -> None:
    match = case.match

    assert match.candidate_id == case.profile.candidate_id
    assert match.job_id == case.job.job_id
    assert case.min_overall <= match.overall_score <= case.max_overall
    assert match.recommendation == case.expected_recommendation
    assert all(detail.reasons for detail in _score_details(case))
    if case.min_evidence_strength is not None:
        assert match.evidence_strength.score >= case.min_evidence_strength
    if case.max_evidence_strength is not None:
        assert match.evidence_strength.score <= case.max_evidence_strength
    if case.min_compensation_alignment is not None:
        assert match.compensation_alignment.score >= case.min_compensation_alignment
    if case.max_compensation_alignment is not None:
        assert match.compensation_alignment.score <= case.max_compensation_alignment
    for term in case.required_disqualifier_terms:
        assert any(term.lower() in item.lower() for item in match.hard_disqualifiers)


def _score_details(case: MatchRegressionCase):
    match = case.match
    return [
        match.qualification_fit,
        match.evidence_strength,
        match.seniority_alignment,
        match.compensation_alignment,
        match.preference_fit,
        match.competitiveness,
    ]


@pytest.mark.eval
@pytest.mark.parametrize("case", match_regression_cases(), ids=lambda case: case.name)
def test_match_regression_case_invariants(case: MatchRegressionCase) -> None:
    _assert_match_invariants(case)
