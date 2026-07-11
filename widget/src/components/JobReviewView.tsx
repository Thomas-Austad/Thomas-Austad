import { FormEvent, useState } from "react";

import type { CompensationEstimate, JobListing, JobMatch, JobSearchResult } from "../contracts";
import { loadCompensation, loadJobMatch, searchJobs, type JobToolClient } from "../jobClient";
import { StatusPanel } from "./StatusPanel";

interface JobReviewViewProps {
  client?: JobToolClient;
}

function toList(value: string): string[] {
  return value.split(/[\n,]/).map((item) => item.trim()).filter(Boolean);
}

function formatMoney(value: number | null | undefined, currency: string): string {
  return value === null || value === undefined
    ? "Not provided"
    : new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
}

export function JobReviewView({ client }: JobReviewViewProps) {
  const [greenhouseBoards, setGreenhouseBoards] = useState("");
  const [leverCompanies, setLeverCompanies] = useState("");
  const [keywords, setKeywords] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [result, setResult] = useState<JobSearchResult>();
  const [selectedJob, setSelectedJob] = useState<JobListing>();
  const [match, setMatch] = useState<JobMatch>();
  const [compensation, setCompensation] = useState<CompensationEstimate>();
  const [roleFamily, setRoleFamily] = useState("");
  const [geography, setGeography] = useState("");
  const [status, setStatus] = useState<"empty" | "error" | "loading" | "ready">("ready");
  const [detail, setDetail] = useState("");

  const runSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!client) {
      setStatus("error");
      setDetail("A secure widget connection is unavailable. No job search was requested.");
      return;
    }
    setStatus("loading");
    setDetail("Searching supported job sources.");
    try {
      const nextResult = await searchJobs(client, {
        greenhouse_boards: toList(greenhouseBoards),
        lever_companies: toList(leverCompanies),
        title_keywords: toList(keywords)
      });
      setResult(nextResult);
      setSelectedJob(undefined);
      setMatch(undefined);
      setCompensation(undefined);
      if (nextResult.jobs.length === 0) {
        setStatus("empty");
        setDetail("No jobs matched this search. Update the supported source names or keywords and try again.");
      } else {
        setStatus("ready");
        setDetail("");
      }
    } catch {
      setStatus("error");
      setDetail("The job search could not be completed. Existing results remain available.");
    }
  };

  const inspectJob = (job: JobListing) => {
    setSelectedJob(job);
    setMatch(undefined);
    setCompensation(undefined);
    setRoleFamily(job.title);
    setGeography(job.location ?? "");
    setStatus("ready");
    setDetail("");
  };

  const reviewMatch = async () => {
    if (!client || !selectedJob || !candidateId.trim()) {
      setStatus("error");
      setDetail("Enter a candidate ID before reviewing a match.");
      return;
    }
    setStatus("loading");
    setDetail("Reviewing the match explanation.");
    try {
      setMatch(await loadJobMatch(client, candidateId, selectedJob.job_id));
      setStatus("ready");
      setDetail("");
    } catch {
      setStatus("error");
      setDetail("The match explanation could not be loaded. Your selected job remains available.");
    }
  };

  const reviewCompensation = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!client || !candidateId.trim() || !roleFamily.trim() || !geography.trim()) {
      setStatus("error");
      setDetail("Enter a candidate ID, role family, and geography before estimating compensation.");
      return;
    }
    setStatus("loading");
    setDetail("Loading compensation assumptions.");
    try {
      setCompensation(await loadCompensation(client, candidateId, roleFamily, geography));
      setStatus("ready");
      setDetail("");
    } catch {
      setStatus("error");
      setDetail("The compensation estimate could not be loaded. Your selected job remains available.");
    }
  };

  return (
    <section aria-labelledby="job-view-title" className="job-view">
      <h2 id="job-view-title">Jobs and fit review</h2>
      <p>Search supported sources, then inspect the job text, match explanation, and compensation assumptions before preparing an application.</p>
      <form className="search-form" onSubmit={runSearch}>
        <label htmlFor="greenhouse-boards">Greenhouse boards (comma or line separated)</label>
        <textarea id="greenhouse-boards" maxLength={6_424} onChange={(event) => setGreenhouseBoards(event.target.value)} value={greenhouseBoards} />
        <label htmlFor="lever-companies">Lever companies (comma or line separated)</label>
        <textarea id="lever-companies" maxLength={6_424} onChange={(event) => setLeverCompanies(event.target.value)} value={leverCompanies} />
        <label htmlFor="job-keywords">Title keywords (comma or line separated)</label>
        <input id="job-keywords" maxLength={5_139} onChange={(event) => setKeywords(event.target.value)} value={keywords} />
        <button className="primary" disabled={status === "loading"} type="submit">Search jobs</button>
      </form>
      <StatusPanel detail={detail} kind={status} />
      {result?.provider_errors.length ? (
        <section aria-live="polite" className="provider-warning" role="status">
          <strong>Some sources were unavailable.</strong>
          <p>Results from other sources are still shown. Unavailable provider: {result.provider_errors.map((error) => error.provider).join(", ")}.</p>
        </section>
      ) : null}
      {result?.jobs.length ? (
        <section aria-labelledby="job-results-title">
          <h3 id="job-results-title">Search results</h3>
          <ul className="job-results">
            {result.jobs.map((job) => (
              <li key={job.job_id}>
                <strong>{job.title}</strong> at {job.company} ({job.location ?? "Location not provided"})
                <button onClick={() => inspectJob(job)} type="button">Inspect job</button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {selectedJob ? (
        <JobDetails
          candidateId={candidateId}
          compensation={compensation}
          geography={geography}
          job={selectedJob}
          match={match}
          onCandidateIdChange={setCandidateId}
          onCompensation={reviewCompensation}
          onGeographyChange={setGeography}
          onMatch={() => void reviewMatch()}
          onRoleFamilyChange={setRoleFamily}
          roleFamily={roleFamily}
        />
      ) : null}
    </section>
  );
}

interface JobDetailsProps {
  candidateId: string;
  compensation?: CompensationEstimate;
  geography: string;
  job: JobListing;
  match?: JobMatch;
  onCandidateIdChange: (value: string) => void;
  onCompensation: (event: FormEvent<HTMLFormElement>) => void;
  onGeographyChange: (value: string) => void;
  onMatch: () => void;
  onRoleFamilyChange: (value: string) => void;
  roleFamily: string;
}

function JobDetails(props: JobDetailsProps) {
  const { job } = props;
  return (
    <div className="job-details">
      <section aria-labelledby="job-detail-title">
        <h3 id="job-detail-title">{job.title} at {job.company}</h3>
        <dl>
          <dt>Source</dt><dd>{job.source}</dd>
          <dt>Location</dt><dd>{job.location ?? "Not provided"}</dd>
          <dt>Work arrangement</dt><dd>{job.remote_type ?? "Not provided"}</dd>
          <dt>Salary range</dt><dd>{formatMoney(job.salary_min, job.currency)} – {formatMoney(job.salary_max, job.currency)}</dd>
        </dl>
        <h4>Job description</h4>
        <p className="job-description">{job.description}</p>
      </section>
      <section aria-labelledby="match-actions-title" className="review-actions">
        <h3 id="match-actions-title">Fit review</h3>
        <label htmlFor="job-candidate-id">Candidate ID</label>
        <input id="job-candidate-id" maxLength={128} onChange={(event) => props.onCandidateIdChange(event.target.value)} value={props.candidateId} />
        <button className="primary" onClick={props.onMatch} type="button">Review match</button>
        {props.match ? <MatchDetails match={props.match} /> : null}
      </section>
      <form aria-labelledby="compensation-title" className="compensation-form" onSubmit={props.onCompensation}>
        <h3 id="compensation-title">Compensation assumptions</h3>
        <label htmlFor="role-family">Role family</label>
        <input id="role-family" maxLength={256} onChange={(event) => props.onRoleFamilyChange(event.target.value)} required value={props.roleFamily} />
        <label htmlFor="geography">Geography</label>
        <input id="geography" maxLength={256} onChange={(event) => props.onGeographyChange(event.target.value)} required value={props.geography} />
        <button className="primary" type="submit">Estimate compensation</button>
        {props.compensation ? <CompensationDetails estimate={props.compensation} /> : null}
      </form>
    </div>
  );
}

function MatchDetails({ match }: { match: JobMatch }) {
  const dimensions = [
    ["Qualification fit", match.qualification_fit], ["Evidence strength", match.evidence_strength],
    ["Seniority alignment", match.seniority_alignment], ["Compensation alignment", match.compensation_alignment],
    ["Preference fit", match.preference_fit], ["Competitiveness", match.competitiveness]
  ] as const;
  return (
    <section aria-labelledby="match-result-title" className="match-result">
      <h4 id="match-result-title">Match: {Math.round(match.overall_score)}% — {match.recommendation}</h4>
      <ul>{dimensions.map(([label, detail]) => <li key={label}><strong>{label}: {Math.round(detail.score)}%</strong> {detail.reasons.join(" ")}</li>)}</ul>
      <h5>Gaps</h5>
      {match.gaps.length ? <ul>{match.gaps.map((gap) => <li key={gap}>{gap}</li>)}</ul> : <p>No gaps recorded.</p>}
      <h5>Hard disqualifiers</h5>
      {match.hard_disqualifiers.length ? <ul>{match.hard_disqualifiers.map((item) => <li key={item}>{item}</li>)}</ul> : <p>None recorded.</p>}
    </section>
  );
}

function CompensationDetails({ estimate }: { estimate: CompensationEstimate }) {
  return (
    <section aria-labelledby="compensation-result-title">
      <h4 id="compensation-result-title">Estimated base range</h4>
      <p>{formatMoney(estimate.base_low, "USD")} – {formatMoney(estimate.base_high, "USD")} (midpoint {formatMoney(estimate.base_mid, "USD")})</p>
      <p>{Math.round(estimate.confidence * 100)}% confidence as of {estimate.as_of}.</p>
      <h5>Assumptions</h5>
      <ul>{estimate.rationale.map((item) => <li key={item}>{item}</li>)}</ul>
    </section>
  );
}
