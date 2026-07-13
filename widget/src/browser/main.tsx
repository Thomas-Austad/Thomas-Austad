import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { App } from "../App";
import { RestToolClient } from "./restClient";
import { ConfirmationDialog } from "../components/ConfirmationDialog";
import { extractResumeFromFile } from "./resumeUpload";
import { profileCreationFailureMessage } from "./profileCreation";
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
      setStatus(profileCreationFailureMessage(response.status));
      return;
    }
    setCandidateId(nextCandidateId);
    setStatus("");
  };

  const uploadResume = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !csrfToken) return;
    setStatus("Reading your resume so you can review the text before creating a profile.");
    try {
      setResumeText(await extractResumeFromFile(file, csrfToken));
      setStatus("Resume text is ready for your review. Nothing has been sent to an employer.");
    } catch {
      setStatus("Your resume could not be read. Choose a DOCX or PDF file under 5 MB, or paste the text instead.");
    } finally {
      event.target.value = "";
    }
  };

  if (!csrfToken || !candidateId) {
    return <main className="widget-shell"><header><p className="eyebrow">Talent Advisor</p><h1>Start your career workspace</h1><p>Upload a resume or paste its text to create a private profile you can review and correct. Nothing is sent to an employer.</p></header>
      {csrfToken ? <form className="candidate-form" onSubmit={(event) => void createProfile(event)}><label htmlFor="resume-file">Resume file (DOCX or PDF)</label><input accept=".docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" id="resume-file" onChange={(event) => void uploadResume(event)} type="file" /><p>The file is read only to extract text and is not stored. Review the extracted text below before continuing.</p><label htmlFor="resume-text">Resume text</label><textarea id="resume-text" maxLength={50_000} onChange={(event) => setResumeText(event.target.value)} required value={resumeText} /><label htmlFor="linkedin-text">LinkedIn text (optional)</label><textarea id="linkedin-text" maxLength={50_000} onChange={(event) => setLinkedinText(event.target.value)} value={linkedinText} /><button className="primary" disabled={!resumeText.trim()} type="submit">Create profile for review</button></form> : null}
      <p aria-live="polite" role="status">{status}</p></main>;
  }
  const client = new RestToolClient(csrfToken);
  return <><App applicationClient={client} browserMode candidateId={candidateId} jobClient={client} onDownloadResume={(applicationId) => client.downloadResume(applicationId)} profileClient={client} />
    <PrivacyControls candidateId={candidateId} client={client} onDeleted={() => setCandidateId(undefined)} /></>;
}

function PrivacyControls({ candidateId, client, onDeleted }: { candidateId: string; client: RestToolClient; onDeleted: () => void }) {
  const [dueCount, setDueCount] = useState<number>();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmPurge, setConfirmPurge] = useState(false);
  const [status, setStatus] = useState("");
  return <section className="widget-shell" aria-labelledby="privacy-controls-title">
    <h2 id="privacy-controls-title">Privacy and data controls</h2>
    <p>These actions affect only your local Talent Advisor data. They do not contact an employer or submit an application.</p>
    <button type="button" onClick={() => void client.retentionReview().then((count) => { setDueCount(count); setStatus(count ? `${count} saved profile${count === 1 ? " is" : "s are"} due for deletion.` : "No saved profiles are due for deletion."); }).catch(() => setStatus("Your saved-data review could not be loaded."))}>Review saved-data retention</button>
    {dueCount ? <button type="button" onClick={() => setConfirmPurge(true)}>Review retention purge</button> : null}
    <button type="button" onClick={() => setConfirmDelete(true)}>Delete current profile</button>
    <p aria-live="polite" role="status">{status}</p>
    <ConfirmationDialog description="Delete your current local profile and its saved evidence? This cannot be undone and does not submit an application." onCancel={() => setConfirmDelete(false)} onConfirm={() => { setConfirmDelete(false); void client.callTool("delete_candidate_profile", { candidate_id: candidateId }).then(() => { setStatus("Your current local profile was deleted."); onDeleted(); }).catch(() => setStatus("Your current profile could not be deleted.")); }} open={confirmDelete} title="Confirm profile deletion" />
    <ConfirmationDialog description={`Delete ${dueCount ?? 0} saved profile${dueCount === 1 ? "" : "s"} that are past the retention period? This cannot be undone.`} onCancel={() => setConfirmPurge(false)} onConfirm={() => { setConfirmPurge(false); void client.purgeRetention().then(() => { setDueCount(0); setStatus("Due saved profiles were deleted."); }).catch(() => setStatus("The saved-data purge could not be completed.")); }} open={confirmPurge} title="Confirm retention purge" />
  </section>;
}

createRoot(document.getElementById("root")!).render(<BrowserWorkspace />);
