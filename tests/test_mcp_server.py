import pytest

from app import store
from app import mcp_server
from app.models.schemas import ConfirmedScreeningAnswer, ProfileCorrectionRequest, ScreeningQuestionReview
from app.services.audit_service import read_audit_events


def test_widget_resource_requires_built_assets(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mcp_server, "WIDGET_DIST_DIR", tmp_path)

    with pytest.raises(RuntimeError, match="run the widget build first"):
        mcp_server.load_widget_resource()


def test_widget_resource_inlines_local_built_assets(tmp_path, monkeypatch) -> None:
    (tmp_path / "talent-advisor-widget.js").write_text("window.widgetReady = true;", encoding="utf-8")
    (tmp_path / "talent-advisor-widget.css").write_text(":host { display: block; }", encoding="utf-8")
    monkeypatch.setattr(mcp_server, "WIDGET_DIST_DIR", tmp_path)

    resource = mcp_server.load_widget_resource()

    assert "talent-advisor-widget" in resource
    assert "window.widgetReady = true;" in resource
    assert "display: block" in resource
    assert "LOCAL_ACCESS_TOKEN" not in resource
    assert "src=" not in resource


def test_widget_resource_csp_denies_external_domains() -> None:
    csp = mcp_server.WIDGET_RESOURCE_META["ui"]["csp"]

    assert csp == {"connectDomains": [], "frameDomains": [], "resourceDomains": []}


def test_profile_correction_uses_the_widget_template() -> None:
    tool = mcp_server.mcp._tool_manager.get_tool("correct_candidate_profile")

    assert tool is not None
    assert tool.meta == mcp_server.WIDGET_TEMPLATE_META


def test_application_review_tools_use_the_widget_template() -> None:
    for name in (
        "get_application_review",
        "resolve_application_screening_answer",
        "approve_prepared_application_review",
    ):
        tool = mcp_server.mcp._tool_manager.get_tool(name)
        assert tool is not None
        assert tool.meta == mcp_server.WIDGET_TEMPLATE_META


async def test_profile_correction_requires_direct_confirmation() -> None:
    with pytest.raises(ValueError, match="direct user confirmation"):
        await mcp_server.correct_candidate_profile(
            "candidate-1",
            ProfileCorrectionRequest(headline="Corrected headline"),
            confirmed_by_user=False,
        )


async def test_application_mcp_writes_require_direct_confirmation() -> None:
    with pytest.raises(ValueError, match="Sensitive screening answers require direct user confirmation"):
        await mcp_server.resolve_application_screening_answer(
            "application-1",
            "Are you authorized to work?",
            "Yes",
            confirmed_by_user=False,
            idempotency_key="12345678-1234-4234-9234-123456789012",
        )
    with pytest.raises(ValueError, match="Application approval requires direct user confirmation"):
        await mcp_server.approve_prepared_application_review(
            "application-1",
            confirmed_by_user=False,
            idempotency_key="12345678-1234-4234-9234-123456789012",
        )


async def test_application_mcp_resolution_then_approval_records_audit(sample_application, tmp_path, monkeypatch) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr("app.config.settings.audit_log_path", str(audit_path))
    question = "Are you authorized to work in the United States?"
    sample_application.requires_user_input = [question]
    sample_application.unresolved_screening_questions = [
        ScreeningQuestionReview(
            question=question,
            category="work_authorization",
            reason="This answer requires direct confirmation.",
        )
    ]
    store.applications[sample_application.application_id] = sample_application

    resolved = await mcp_server.resolve_application_screening_answer(
        sample_application.application_id,
        question,
        "Yes",
        confirmed_by_user=True,
        idempotency_key="12345678-1234-4234-9234-123456789012",
    )
    approved = await mcp_server.approve_prepared_application_review(
        sample_application.application_id,
        confirmed_by_user=True,
        idempotency_key="12345678-1234-4234-9234-123456789013",
    )

    assert resolved["unresolved_screening_questions"] == []
    assert approved["status"] == "approved"
    events = read_audit_events(audit_path)
    assert [event.request_id for event in events] == [
        "12345678-1234-4234-9234-123456789012",
        "12345678-1234-4234-9234-123456789013",
    ]
    assert "Yes" not in audit_path.read_text(encoding="utf-8")


async def test_prepared_application_tool_returns_json_compatible_dates(sample_application, monkeypatch) -> None:
    sample_application.confirmed_screening_answers = [
        ConfirmedScreeningAnswer(
            question="Synthetic question",
            category="work_authorization",
            request_id="request-123",
        )
    ]

    async def fake_prepare(_request):
        return sample_application

    monkeypatch.setattr(mcp_server, "prepare_application", fake_prepare)

    package = await mcp_server.prepare_job_application("candidate-1", "job-1")

    assert isinstance(package["confirmed_screening_answers"][0]["confirmed_at"], str)
