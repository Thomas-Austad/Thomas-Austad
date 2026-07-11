import { FormEvent, useState } from "react";

import type { EditableProfileField, ProfileReview } from "../contracts";
import { loadProfileReview, saveProfileCorrection, type ProfileToolClient } from "../profileClient";
import { ConfirmationDialog } from "./ConfirmationDialog";
import { StatusPanel } from "./StatusPanel";

interface ProfileReviewViewProps {
  client?: ProfileToolClient;
  candidateId?: string;
}

const fieldLabels: Record<EditableProfileField, string> = {
  name: "Name",
  headline: "Headline",
  current_level: "Current level"
};

function displayValue(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value);
}

export function ProfileReviewView({ client, candidateId: suppliedCandidateId }: ProfileReviewViewProps) {
  const [candidateId, setCandidateId] = useState(suppliedCandidateId ?? "");
  const [field, setField] = useState<EditableProfileField>("headline");
  const [value, setValue] = useState("");
  const [review, setReview] = useState<ProfileReview>();
  const [status, setStatus] = useState<"error" | "loading" | "ready">("ready");
  const [detail, setDetail] = useState("");
  const [confirmationOpen, setConfirmationOpen] = useState(false);

  const load = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!client) {
      setStatus("error");
      setDetail("A secure widget connection is unavailable. No profile data was requested.");
      return;
    }
    setStatus("loading");
    setDetail("Loading your profile review.");
    try {
      setReview(await loadProfileReview(client, candidateId));
      setStatus("ready");
    } catch {
      setStatus("error");
      setDetail("Your profile review could not be loaded. No profile data was changed.");
    }
  };

  const confirmCorrection = async () => {
    if (!client) {
      return;
    }
    setConfirmationOpen(false);
    setStatus("loading");
    setDetail("Saving your confirmed correction.");
    try {
      setReview(await saveProfileCorrection(client, { candidate_id: candidateId, field, value }));
      setValue("");
      setStatus("ready");
      setDetail("Your correction was saved as user-provided information.");
    } catch {
      setStatus("error");
      setDetail("Your correction could not be saved. No profile data was changed.");
    }
  };

  return (
    <section aria-labelledby="profile-view-title" className="profile-view">
      <h2 id="profile-view-title">Profile review</h2>
      <p>Review evidence and ambiguities before using this profile for job matching or application preparation.</p>
      <form className="candidate-form" onSubmit={load}>
        {suppliedCandidateId ? <p>Your current profile is selected.</p> : <><label htmlFor="candidate-id">Candidate ID</label><input
          autoComplete="off"
          id="candidate-id"
          maxLength={128}
          onChange={(event) => setCandidateId(event.target.value)}
          required
          value={candidateId}
        /></>}
        <button className="primary" disabled={status === "loading"} type="submit">
          Review profile
        </button>
      </form>
      <StatusPanel detail={detail} kind={status} />
      {review ? <ProfileDetails review={review} /> : null}
      {review ? (
        <form
          className="correction-form"
          onSubmit={(event) => {
            event.preventDefault();
            setConfirmationOpen(true);
          }}
        >
          <h3>Correct profile information</h3>
          <p>Corrections are labelled as user-provided. They do not create new evidence or submit an application.</p>
          <label htmlFor="correction-field">Field</label>
          <select id="correction-field" onChange={(event) => setField(event.target.value as EditableProfileField)} value={field}>
            {Object.entries(fieldLabels).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
          <label htmlFor="correction-value">Corrected {fieldLabels[field]}</label>
          <textarea id="correction-value" maxLength={2_000} onChange={(event) => setValue(event.target.value)} required value={value} />
          <button className="primary" disabled={status === "loading" || value.trim().length === 0} type="submit">
            Review correction
          </button>
        </form>
      ) : null}
      <ConfirmationDialog
        description={`Save your user-provided ${fieldLabels[field].toLowerCase()} correction exactly as shown? This changes only your local profile.`}
        onCancel={() => setConfirmationOpen(false)}
        onConfirm={() => void confirmCorrection()}
        open={confirmationOpen}
        title="Confirm profile correction"
      />
    </section>
  );
}

function ProfileDetails({ review }: { review: ProfileReview }) {
  const { profile } = review;
  return (
    <div className="profile-details">
      <section aria-labelledby="generated-profile-title">
        <h3 id="generated-profile-title">Evidence-grounded profile</h3>
        <dl>
          <dt>Name</dt><dd>{profile.name ?? "Not provided"}</dd>
          <dt>Headline</dt><dd>{profile.headline}</dd>
          <dt>Current level</dt><dd>{profile.current_level}</dd>
          <dt>Primary functions</dt><dd>{profile.primary_functions.join(", ") || "Not provided"}</dd>
          <dt>Skills</dt><dd>{profile.skills.map((skill) => skill.name).join(", ") || "Not provided"}</dd>
          <dt>Experience</dt><dd>{profile.experience.map((item) => `${item.title} at ${item.employer}`).join("; ") || "Not provided"}</dd>
          <dt>Education</dt><dd>{profile.education.join("; ") || "Not provided"}</dd>
          <dt>Certifications</dt><dd>{profile.certifications.join("; ") || "Not provided"}</dd>
        </dl>
      </section>
      <section aria-labelledby="ambiguities-title">
        <h3 id="ambiguities-title">Ambiguities to review</h3>
        {profile.ambiguities.length ? <ul>{profile.ambiguities.map((item) => <li key={item}>{item}</li>)}</ul> : <p>None recorded.</p>}
      </section>
      <section aria-labelledby="evidence-title">
        <h3 id="evidence-title">Source evidence</h3>
        {review.evidence.length ? (
          <ul className="evidence-list">
            {review.evidence.map((evidence) => (
              <li key={`${evidence.claim_type}-${evidence.claim_ref}-${evidence.source_ref ?? ""}`}>
                <strong>{evidence.claim_type}</strong> from {evidence.source}: {evidence.text} ({Math.round(evidence.confidence * 100)}% confidence)
              </li>
            ))}
          </ul>
        ) : <p>No source evidence is available.</p>}
      </section>
      <section aria-labelledby="corrections-title">
        <h3 id="corrections-title">Past user-provided corrections</h3>
        {review.corrections.length ? (
          <ul>
            {review.corrections.map((correction) => <li key={correction.correction_id}>{correction.field}: {displayValue(correction.value)}</li>)}
          </ul>
        ) : <p>No past corrections.</p>}
      </section>
    </div>
  );
}
