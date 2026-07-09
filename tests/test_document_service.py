from app.services.document_service import markdown_resume_to_docx


def test_docx_generation():
    result = markdown_resume_to_docx("# Jane Doe\n## Experience\n- Improved throughput 20%")
    assert result[:2] == b"PK"
