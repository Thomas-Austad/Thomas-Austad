from bs4 import BeautifulSoup
from urllib.parse import quote

from app.connectors.http import fetch_provider_json
from app.models.schemas import JobListing


class GreenhouseConnector:
    async def fetch_board(self, board_token: str) -> list[JobListing]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{quote(board_token, safe='')}/jobs"
        data = await fetch_provider_json(url, params={"content": "true"})
        if not isinstance(data, dict):
            raise ValueError("Greenhouse response is not an object")
        jobs = []
        for item in data.get("jobs", []):
            description = BeautifulSoup(item.get("content", ""), "html.parser").get_text(" ", strip=True)
            jid = f"greenhouse:{board_token}:{item['id']}"
            jobs.append(JobListing(
                job_id=jid, source="greenhouse", source_url=item["absolute_url"],
                company=board_token.replace("-", " ").title(), title=item["title"],
                location=(item.get("location") or {}).get("name"), description=description,
                posted_at=item.get("updated_at"), raw=item,
            ))
        return jobs
