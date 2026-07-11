import { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { App } from "../App";
import { RestToolClient } from "./restClient";
import "../styles.css";

function BrowserWorkspace() {
  const [csrfToken, setCsrfToken] = useState<string>();
  const [candidateId, setCandidateId] = useState<string>();
  const [resumeText, setResumeText] = useState("");
  const [linkedinText, setLinkedinText] = useState("");
  const [status, setStatus] = useState("Preparing your private workspace.");

  useEffect(() => {
    const bootstrap = new URLSearchParams(window.location.hash.slice(1)).get("bootstrap");
    window.history.replaceState(null, "", "/app");
    if (!bootstrap) {
      setStatus("Open Talent Advisor from the local launcher to begin.");
      return;
    }
    void fetch("/browser-session/bootstrap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bootstrap_token: bootstrap })
    }).then(async (response) => {
      if (!response.ok) throw new Error();
      return response.json() as Promise<{ csrf_token: string }>;
    }).then(({ csrf_token }) => {
      setCsrfToken(csrf_token);
      setStatus("");
    }).catch(() => setStatus("This startup link has expired. Open Talent Advisor again from the local launcher."));
  }, []);

  const createProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!csrfToken || !resumeText.trim()) return;
    setStatus("Creating an evidence-grounded profile for your review.");
    const nextCandidateId = `local-${crypto.randomUUID()}`;
    const response = await fetch("/profiles", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: JSON.stringify({ candidate_id: nextCandidateId, resume_text: resumeText, linkedin_text: linkedinText })
    });
    if (!response.ok) {
      setStatus("Your profile could not be created. Your text is still here so you can try again.");
      return;
    }
    setCandidateId(nextCandidateId);
    setStatus("");
  };

  if (!csrfToken || !candidateId) {
    return <main className="widget-shell"><header><p className="eyebrow">Talent Advisor</p><h1>Start your career workspace</h1><p>Paste your resume to create a private profile you can review and correct. Nothing is sent to an employer.</p></header>
      {csrfToken ? <form className="candidate-form" onSubmit={(event) => void createProfile(event)}><label htmlFor="resume-text">Resume text</label><textarea id="resume-text" maxLength={50_000} onChange={(event) => setResumeText(event.target.value)} required value={resumeText} /><label htmlFor="linkedin-text">LinkedIn text (optional)</label><textarea id="linkedin-text" maxLength={50_000} onChange={(event) => setLinkedinText(event.target.value)} value={linkedinText} /><button className="primary" disabled={!resumeText.trim()} type="submit">Create profile for review</button></form> : null}
      <p aria-live="polite" role="status">{status}</p></main>;
  }
  const client = new RestToolClient(csrfToken);
  return <App applicationClient={client} candidateId={candidateId} jobClient={client} profileClient={client} />;
}

createRoot(document.getElementById("root")!).render(<BrowserWorkspace />);
