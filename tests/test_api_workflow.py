from fastapi.testclient import TestClient

from app import store
from app.main import app
from app.models.schemas import JobListing, ScreeningQuestionReview
from app.services.audit_service import read_audit_events


def test_core_api_workflow_uses_stored_state(
    monkeypatch,
    sample_application,
    sample_compensation,
    sample_job,
    sample_match,
    sample_profile,
):
    async def profile_run(self, candidate_id, resume_text, linkedin_text, preferences):
        assert candidate_id == sample_profile.candidate_id
        assert "Python" in resume_text
        return sample_profile

    async def search_known_boards(self, greenhouse_boards, lever_companies):
        assert greenhouse_boards == ["example"]
        assert lever_companies == []
        return [sample_job]

    async def match_run(self, profile, job):
        assert profile == sample_profile
        assert job == sample_job
        return sample_match

    async def compensation_run(self, profile, role_family, geography, comparable):
        assert profile == sample_profile
        assert role_family == "Backend Engineering"
        assert geography == "Remote US"
        assert comparable == [sample_job]
        return sample_compensation

    async def application_prepare(self, profile, job, screening_questions):
        assert profile == sample_profile
        assert job == sample_job
        assert screening_questions == []
        return sample_application

    monkeypatch.setattr("app.services.openai_service.OpenAIService.__init__", lambda self: None)
    monkeypatch.setattr("app.main.CandidateProfileAgent.run", profile_run)
    monkeypatch.setattr("app.main.JobService.search_known_boards", search_known_boards)
    monkeypatch.setattr("app.main.MatchAgent.run", match_run)
    monkeypatch.setattr("app.main.CompensationAgent.run", compensation_run)
    monkeypatch.setattr("app.main.ApplicationAgent.prepare", application_prepare)

    client = TestClient(app)

    profile_response = client.post(
        "/profiles",
        json={
            "candidate_id": sample_profile.candidate_id,
            "resume_text": "Python platform engineer",
            "preferences": {"remote_preference": "remote"},
        },
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["candidate_id"] == sample_profile.candidate_id
    assert store.profiles[sample_profile.candidate_id] == sample_profile

    jobs_response = client.post(
        "/jobs/search",
        json={"greenhouse_boards": ["example"], "title_keywords": ["backend"]},
    )
    assert jobs_response.status_code == 200
    assert jobs_response.json()["count"] == 1
    assert store.jobs[sample_job.job_id] == sample_job

    match_response = client.post(f"/matches/{sample_profile.candidate_id}/{sample_job.job_id}")
    assert match_response.status_code == 200
    assert match_response.json()["overall_score"] == 85
    assert store.matches[(sample_profile.candidate_id, sample_job.job_id)] == sample_match

    compensation_response = client.post(
        f"/compensation/{sample_profile.candidate_id}",
        params={"role_family": "Backend Engineering", "geography": "Remote US"},
    )
    assert compensation_response.status_code == 200
    assert compensation_response.json()["base_mid"] == 170000

    application_response = client.post(
        "/applications/prepare",
        json={"candidate_id": sample_profile.candidate_id, "job_id": sample_job.job_id},
    )
    assert application_response.status_code == 200
    assert application_response.json()["application_id"] == sample_application.application_id
    assert store.applications[sample_application.application_id] == sample_application

    approval_response = client.post(f"/applications/{sample_application.application_id}/approve")
    assert approval_response.status_code == 200
    assert approval_response.json()["status"] == "approved"


def test_missing_records_return_not_found(sample_profile):
    client = TestClient(app)

    match_response = client.post(f"/matches/{sample_profile.candidate_id}/missing-job")
    assert match_response.status_code == 404
    assert match_response.json()["detail"] == "Candidate or job not found"

    compensation_response = client.post(
        f"/compensation/{sample_profile.candidate_id}",
        params={"role_family": "Backend Engineering", "geography": "Remote US"},
    )
    assert compensation_response.status_code == 404
    assert compensation_response.json()["detail"] == "Candidate not found"

    application_response = client.post(
        "/applications/prepare",
        json={"candidate_id": sample_profile.candidate_id, "job_id": "missing-job"},
    )
    assert application_response.status_code == 404
    assert application_response.json()["detail"] == "Candidate or job not found"

    approval_response = client.post("/applications/missing-application/approve")
    assert approval_response.status_code == 404
    assert approval_response.json()["detail"] == "Application not found"


def test_approval_requires_resolved_user_input(sample_application, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.audit_log_path", str(tmp_path / "audit.jsonl"))
    sample_application.requires_user_input = ["Confirm work authorization directly with the user."]
    store.applications[sample_application.application_id] = sample_application

    response = TestClient(app).post(f"/applications/{sample_application.application_id}/approve")

    assert response.status_code == 409
    assert response.json()["detail"] == "Resolve required user inputs before approval"
    assert store.applications[sample_application.application_id].status == "prepared"
    assert read_audit_events(tmp_path / "audit.jsonl") == []


def test_approval_requires_resolved_sensitive_screening_questions(
    sample_application,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr("app.config.settings.audit_log_path", str(tmp_path / "audit.jsonl"))
    sample_application.unresolved_screening_questions = [
        ScreeningQuestionReview(
            question="Are you authorized to work in the United States?",
            category="work_authorization",
            reason="Work authorization answers require direct user confirmation.",
        )
    ]
    store.applications[sample_application.application_id] = sample_application

    response = TestClient(app).post(f"/applications/{sample_application.application_id}/approve")

    assert response.status_code == 409
    assert response.json()["detail"] == "Resolve required user inputs before approval"
    assert store.applications[sample_application.application_id].status == "prepared"
    assert read_audit_events(tmp_path / "audit.jsonl") == []


def test_sensitive_screening_question_resolution_requires_direct_confirmation(
    sample_application,
):
    question = "Are you authorized to work in the United States?"
    sample_application.requires_user_input = [question]
    sample_application.unresolved_screening_questions = [
        ScreeningQuestionReview(
            question=question,
            category="work_authorization",
            reason="Work authorization answers require direct user confirmation.",
        )
    ]
    store.applications[sample_application.application_id] = sample_application

    response = TestClient(app).post(
        f"/applications/{sample_application.application_id}/screening-questions/resolve",
        json={
            "question": question,
            "answer": "Yes",
            "confirmed_by_user": False,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Sensitive screening answers require direct user confirmation"
    )
    stored = store.applications[sample_application.application_id]
    assert stored.screening_answers == {}
    assert stored.requires_user_input == [question]
    assert len(stored.unresolved_screening_questions) == 1


def test_resolving_sensitive_screening_question_unblocks_approval(
    sample_application,
    tmp_path,
    monkeypatch,
):
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr("app.config.settings.audit_log_path", str(audit_path))
    question = "Are you authorized to work in the United States?"
    sample_application.requires_user_input = [question]
    sample_application.unresolved_screening_questions = [
        ScreeningQuestionReview(
            question=question,
            category="work_authorization",
            reason="Work authorization answers require direct user confirmation.",
        )
    ]
    store.applications[sample_application.application_id] = sample_application
    client = TestClient(app)

    resolution_response = client.post(
        f"/applications/{sample_application.application_id}/screening-questions/resolve",
        json={
            "question": question,
            "answer": "Yes",
            "confirmed_by_user": True,
        },
        headers={"x-request-id": "resolve-request-123"},
    )
    approval_response = client.post(
        f"/applications/{sample_application.application_id}/approve",
        headers={"x-request-id": "approve-request-123"},
    )

    assert resolution_response.status_code == 200
    resolution_body = resolution_response.json()
    assert resolution_body["screening_answers"] == {question: "Yes"}
    assert resolution_body["requires_user_input"] == []
    assert resolution_body["unresolved_screening_questions"] == []
    assert resolution_body["confirmed_screening_answers"][0]["question"] == question
    assert resolution_body["confirmed_screening_answers"][0]["category"] == "work_authorization"
    assert resolution_body["confirmed_screening_answers"][0]["request_id"] == (
        "resolve-request-123"
    )
    assert approval_response.status_code == 200
    assert approval_response.json()["status"] == "approved"
    events = read_audit_events(audit_path)
    assert len(events) == 1
    assert events[0].request_id == "approve-request-123"


def test_approval_records_non_sensitive_audit_event(sample_application, tmp_path, monkeypatch):
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr("app.config.settings.audit_log_path", str(audit_path))
    store.applications[sample_application.application_id] = sample_application

    response = TestClient(app).post(
        f"/applications/{sample_application.application_id}/approve",
        headers={"x-request-id": "request-123"},
    )

    assert response.status_code == 200
    events = read_audit_events(audit_path)
    assert len(events) == 1
    assert events[0].action == "application.approve"
    assert events[0].target_id == sample_application.application_id
    assert events[0].result == "approved"
    assert events[0].request_id == "request-123"


def test_job_search_title_keywords_filter_results(monkeypatch, sample_job):
    other_job = JobListing(
        job_id="lever:example:2",
        source="lever",
        source_url="https://example.com/jobs/2",
        company="Example Co",
        title="Product Designer",
        description="Design user-facing workflows.",
    )

    async def search_known_boards(self, greenhouse_boards, lever_companies):
        return [sample_job, other_job]

    monkeypatch.setattr("app.main.JobService.search_known_boards", search_known_boards)

    response = TestClient(app).post(
        "/jobs/search",
        json={"greenhouse_boards": ["example"], "title_keywords": ["backend"]},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["jobs"][0]["job_id"] == sample_job.job_id
    assert list(store.jobs) == [sample_job.job_id]

