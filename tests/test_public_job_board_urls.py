import pytest

from app.main import _parse_public_job_board_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://boards.greenhouse.io/example", ("greenhouse", "example")),
        ("https://jobs.lever.co/example", ("lever", "example")),
        ("https://jobs.ashbyhq.com/example", ("ashby", "example")),
    ],
)
def test_supported_public_job_board_urls_are_reduced_to_connector_keys(url: str, expected: tuple[str, str]) -> None:
    assert _parse_public_job_board_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://boards.greenhouse.io/example",
        "https://127.0.0.1/example",
        "https://boards.greenhouse.io/example/extra",
        "https://user@jobs.lever.co/example",
        "https://jobs.ashbyhq.com/%2e%2e",
    ],
)
def test_public_job_board_parser_rejects_untrusted_or_ambiguous_urls(url: str) -> None:
    with pytest.raises(ValueError, match="supported public careers-board link"):
        _parse_public_job_board_url(url)
