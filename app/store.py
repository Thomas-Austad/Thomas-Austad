from app.models.schemas import CandidateProfile, JobListing, JobMatch, ApplicationPackage

# Personal-use MVP store. Replace with PostgreSQL repositories before multi-user deployment.
profiles: dict[str, CandidateProfile] = {}
jobs: dict[str, JobListing] = {}
matches: dict[tuple[str, str], JobMatch] = {}
applications: dict[str, ApplicationPackage] = {}
