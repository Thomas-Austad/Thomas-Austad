import httpx
from bs4 import BeautifulSoup
from app.models.schemas import JobListing


class LeverConnector:
    async def fetch_company(self, company: str) -> list[JobListing]:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        async with httpx.AsyncClient(timeout=30) as client:
            data = (await client.get(url)).raise_for_status().json()
        jobs = []
        for item in data:
            text = item.get("descriptionPlain") or BeautifulSoup(item.get("description", ""), "html.parser").get_text(" ", strip=True)
            jobs.append(JobListing(
                job_id=f"lever:{company}:{item['id']}", source="lever", source_url=item["hostedUrl"],
                company=company.replace("-", " ").title(), title=item["text"],
                location=(item.get("categories") or {}).get("location"),
                employment_type=(item.get("categories") or {}).get("commitment"),
                description=text, raw=item,
            ))
        return jobs
