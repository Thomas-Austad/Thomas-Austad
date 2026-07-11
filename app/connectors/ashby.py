from typing import Any
from urllib.parse import quote

from bs4 import BeautifulSoup

from app.connectors.http import fetch_provider_json
from app.models.schemas import JobListing


def _normalized_employment_type(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("_", "-")
    return {
        "fulltime": "full-time",
        "parttime": "part-time",
    }.get(normalized, normalized or None)


def _normalized_remote_type(item: dict[str, Any]) -> str | None:
    if item.get("isRemote") is True:
        return "remote"
    workplace_type = item.get("workplaceType")
    if not isinstance(workplace_type, str):
        return None
    normalized = workplace_type.strip().lower()
    return normalized if normalized in {"remote", "hybrid", "onsite"} else None


def _annual_salary(compensation: object) -> tuple[int | None, int | None, str]:
    if not isinstance(compensation, dict):
        return None, None, "USD"
    components = compensation.get("summaryComponents")
    if not isinstance(components, list):
        return None, None, "USD"
    for component in components:
        if not isinstance(component, dict):
            continue
        if component.get("compensationType") != "Salary" or component.get("interval") != "YEAR":
            continue
        minimum = component.get("minValue")
        maximum = component.get("maxValue")
        currency = component.get("currencyCode")
        if isinstance(minimum, bool) or isinstance(maximum, bool):
            continue
        if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
            continue
        if not isinstance(currency, str) or len(currency) != 3:
            continue
        return int(minimum), int(maximum), currency.upper()
    return None, None, "USD"


class AshbyConnector:
    async def fetch_job_board(self, job_board_name: str) -> list[JobListing]:
        board_name = quote(job_board_name, safe="")
        data = await fetch_provider_json(
            f"https://api.ashbyhq.com/posting-api/job-board/{board_name}",
            params={"includeCompensation": "true"},
        )
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ValueError("Ashby response does not contain a jobs list")
        jobs: list[JobListing] = []
        for item in data["jobs"]:
            if not isinstance(item, dict) or item.get("isListed") is not True:
                continue
            job_id = item.get("id")
            source_url = item.get("jobUrl")
            title = item.get("title")
            if not all(isinstance(value, str) and value for value in (job_id, source_url, title)):
                continue
            salary_min, salary_max, currency = _annual_salary(item.get("compensation"))
            description = item.get("descriptionPlain")
            if not isinstance(description, str):
                description = BeautifulSoup(
                    str(item.get("descriptionHtml", "")), "html.parser"
                ).get_text(" ", strip=True)
            jobs.append(
                JobListing(
                    job_id=f"ashby:{job_board_name}:{job_id}",
                    source="ashby",
                    source_url=source_url,
                    company=job_board_name.replace("-", " ").title(),
                    title=title,
                    location=item.get("location") if isinstance(item.get("location"), str) else None,
                    remote_type=_normalized_remote_type(item),
                    description=description,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    currency=currency,
                    employment_type=_normalized_employment_type(item.get("employmentType")),
                    posted_at=item.get("publishedAt") if isinstance(item.get("publishedAt"), str) else None,
                    raw=item,
                )
            )
        return jobs
