from app.agents.application_agent import ApplicationAgent, DraftPackage


class FakeAI:
    async def structured(self, system, user, schema):
        assert schema is DraftPackage
        return DraftPackage(
            tailored_resume_markdown="# Synthetic Candidate",
            cover_letter="I am interested in this role.",
            screening_answers={
                "Are you authorized to work in the United States?": "Yes",
                "Will you now or in the future require visa sponsorship?": "No",
                "Why are you interested in this role?": "It matches my platform experience.",
            },
            factual_warnings=[],
            requires_user_input=[],
        )


async def test_application_agent_flags_sensitive_questions_and_removes_guessed_answers(
    sample_job,
    sample_profile,
):
    package = await ApplicationAgent(ai=FakeAI()).prepare(
        sample_profile,
        sample_job,
        [
            "Are you authorized to work in the United States?",
            "Why are you interested in this role?",
        ],
    )

    assert "Are you authorized to work in the United States?" not in package.screening_answers
    assert "Will you now or in the future require visa sponsorship?" not in package.screening_answers
    assert package.screening_answers == {
        "Why are you interested in this role?": "It matches my platform experience."
    }
    assert package.requires_user_input == [
        "Are you authorized to work in the United States?",
        "Will you now or in the future require visa sponsorship?",
    ]
    assert len(package.unresolved_screening_questions) == 2
    assert package.unresolved_screening_questions[0].category == "work_authorization"
    assert package.unresolved_screening_questions[1].category == "work_authorization"
