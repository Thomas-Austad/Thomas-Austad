from datetime import UTC

from app.models.schemas import CandidateProfile


def test_candidate_profile_generated_at_defaults_to_utc_aware_datetime():
    profile = CandidateProfile(
        candidate_id="candidate-123",
        headline="Backend platform engineer",
        current_level="Senior",
        primary_functions=["backend", "platform"],
        skills=[],
        experience=[],
    )

    assert profile.generated_at.tzinfo is not None
    assert profile.generated_at.utcoffset() == UTC.utcoffset(profile.generated_at)

