import { FormEvent, useEffect, useState } from "react";

import type { ApplicationPackage, BrowserHandoff, BrowserHandoffPreview } from "../contracts";
import {
  approveApplication,
  beginBrowserHandoff,
  loadBrowserHandoffPreview,
  loadApplicationReview,
  resolveScreeningAnswer,
  type ApplicationToolClient
} from "../applicationClient";
import { ConfirmationDialog } from "./ConfirmationDialog";
import { StatusPanel } from "./StatusPanel";

interface ApplicationReviewViewProps {
  browserMode?: boolean;
  client?: ApplicationToolClient;
  preparedPackage?: ApplicationPackage;
  onDownloadResume?: (applicationId: string) => Promise<void>;
}

interface PendingScreeningAnswer {
  answer: string;
  question: string;
}

function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

export function ApplicationReviewView({ browserMode = false, client, onDownloadResume, preparedPackage }: ApplicationReviewViewProps) {
  const [applicationId, setApplicationId] = useState("");
  const [packageReview, setPackageReview] = useState<ApplicationPackage>();
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [pendingScreening, setPendingScreening] = useState<PendingScreeningAnswer>();
  const [approvalConfirmationOpen, setApprovalConfirmationOpen] = useState(false);
  const [exportConfirmationOpen, setExportConfirmationOpen] = useState(false);
  const [handoffPreview, setHandoffPreview] = useState<BrowserHandoffPreview>();
  const [browserHandoff, setBrowserHandoff] = useState<BrowserHandoff>();
  const [pendingAction, setPendingAction] = useState<"approve" | "handoff" | "handoff_preview" | "load" | "resolve">();
  const [status, setStatus] = useState<"empty" | "error" | "loading" | "ready">("ready");
  const [detail, setDetail] = useState("");

  useEffect(() => {
    if (!preparedPackage) {
      return;
    }
    setApplicationId(preparedPackage.application_id);
    setPackageReview(preparedPackage);
    setAnswers({});
    setHandoffPreview(undefined);
    setBrowserHandoff(undefined);
    setStatus("ready");
    setDetail("Prepared for your review. This has not been approved or submitted.");
  }, [preparedPackage]);

  const load = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!client) {
      setStatus("error");
      setDetail("A secure widget connection is unavailable. No application package was requested.");
      return;
    }
    setPendingAction("load");
    setStatus("loading");
    setDetail("Loading the prepared application package.");
    try {
      const loaded = await loadApplicationReview(client, applicationId);
      setPackageReview(loaded);
      setAnswers({});
      setHandoffPreview(undefined);
      setBrowserHandoff(undefined);
      setStatus("ready");
      setDetail("");
    } catch {
      setStatus("error");
      setDetail("The application package could not be loaded. No approval or answer was sent.");
    } finally {
      setPendingAction(undefined);
    }
  };

  const startBrowserHandoff = async () => {
    if (!client || !packageReview) {
      return;
    }
    setPendingAction("handoff_preview");
    setStatus("loading");
    setDetail("Checking the employer application page before browser handoff.");
    try {
      const preview = await loadBrowserHandoffPreview(client, packageReview.application_id);
      setHandoffPreview(preview);
      setStatus("ready");
      setDetail("");
    } catch {
      setStatus("error");
      setDetail("Browser handoff is unavailable. No browser was opened and no application was submitted.");
    } finally {
      setPendingAction(undefined);
    }
  };

  const confirmBrowserHandoff = async () => {
    if (!client || !packageReview || !handoffPreview) {
      return;
    }
    setHandoffPreview(undefined);
    setPendingAction("handoff");
    setStatus("loading");
    setDetail("Preparing your confirmed browser handoff. No application is being submitted.");
    try {
      const handoff = await beginBrowserHandoff(client, {
        application_id: packageReview.application_id,
        expected_destination_url: handoffPreview.destination_url,
        idempotency_key: newIdempotencyKey()
      });
      setBrowserHandoff(handoff);
      setStatus("ready");
      setDetail("Your employer-page link is ready. Opening it is your choice and does not submit an application.");
    } catch {
      setStatus("error");
      setDetail("Browser handoff could not be prepared. No browser was opened and no application was submitted.");
    } finally {
      setPendingAction(undefined);
    }
  };

  const confirmScreeningAnswer = async () => {
    if (!client || !packageReview || !pendingScreening) {
      return;
    }
    setPendingScreening(undefined);
    setPendingAction("resolve");
    setStatus("loading");
    setDetail("Saving your directly confirmed screening answer.");
    try {
      const updated = await resolveScreeningAnswer(client, {
        application_id: packageReview.application_id,
        question: pendingScreening.question,
        answer: pendingScreening.answer,
        idempotency_key: newIdempotencyKey()
      });
      setPackageReview(updated);
      setAnswers((current) => ({ ...current, [pendingScreening.question]: "" }));
      setStatus("ready");
      setDetail("Your answer was recorded as directly confirmed by you.");
    } catch {
      setStatus("error");
      setDetail("The screening answer could not be saved. No answer was confirmed.");
    } finally {
      setPendingAction(undefined);
    }
  };

  const confirmApproval = async () => {
    if (!client || !packageReview) {
      return;
    }
    setApprovalConfirmationOpen(false);
    setPendingAction("approve");
    setStatus("loading");
    setDetail("Recording your local approval.");
    try {
      const updated = await approveApplication(client, {
        application_id: packageReview.application_id,
        idempotency_key: newIdempotencyKey()
      });
      if (updated.status !== "approved") {
        throw new Error("Unexpected application approval state");
      }
      setPackageReview(updated);
      setStatus("ready");
      setDetail("The package is approved locally. It has not been submitted to an employer.");
    } catch {
      setStatus("error");
      setDetail("The package could not be approved. It was not submitted to an employer.");
    } finally {
      setPendingAction(undefined);
    }
  };

  const confirmExport = async () => {
    if (!packageReview || !onDownloadResume) return;
    setExportConfirmationOpen(false);
    setPendingAction("load");
    setStatus("loading");
    setDetail("Preparing your confirmed DOCX download.");
    try {
      await onDownloadResume(packageReview.application_id);
      setStatus("ready");
      setDetail("Your DOCX download is ready. Nothing was submitted to an employer.");
    } catch {
      setStatus("error");
      setDetail("The DOCX file could not be prepared. No application was submitted.");
    } finally {
      setPendingAction(undefined);
    }
  };

  const approvalBlocked = !packageReview
    || packageReview.status !== "prepared"
    || packageReview.requires_user_input.length > 0
    || packageReview.unresolved_screening_questions.length > 0;

  return (
    <section aria-labelledby="application-view-title" className="application-view">
      <h2 id="application-view-title">Application review and approval</h2>
      <p>Review a prepared package before approval. Approval is local only and is not an application submission.</p>
      {!browserMode ? <form className="application-load-form" onSubmit={load}>
        <label htmlFor="application-id">Application package ID</label>
        <input
          autoComplete="off"
          id="application-id"
          maxLength={128}
          onChange={(event) => setApplicationId(event.target.value)}
          required
          value={applicationId}
        />
        <button className="primary" disabled={pendingAction !== undefined} type="submit">Load prepared package</button>
      </form> : null}
      <StatusPanel detail={detail} kind={status} />
      {packageReview ? (
        <PackageDetails
          answers={answers}
          approvalBlocked={approvalBlocked}
          browserHandoff={browserHandoff}
          onAnswerChange={(question, answer) => setAnswers((current) => ({ ...current, [question]: answer }))}
          onApprove={() => setApprovalConfirmationOpen(true)}
          onStartBrowserHandoff={() => void startBrowserHandoff()}
          onReviewAnswer={(question) => setPendingScreening({ question, answer: answers[question] ?? "" })}
          onExport={onDownloadResume ? () => setExportConfirmationOpen(true) : undefined}
          packageReview={packageReview}
          pendingAction={pendingAction}
        />
      ) : null}
      <ConfirmationDialog
        description="Download this tailored resume as a DOCX file? This downloads only a local copy and does not submit an application."
        onCancel={() => setExportConfirmationOpen(false)}
        onConfirm={() => void confirmExport()}
        open={exportConfirmationOpen}
        title="Confirm DOCX download"
      />
      <ConfirmationDialog
        description={pendingScreening ? `Save this answer for the screening question “${pendingScreening.question}” as your directly confirmed response? This does not submit an application.` : ""}
        onCancel={() => setPendingScreening(undefined)}
        onConfirm={() => void confirmScreeningAnswer()}
        open={pendingScreening !== undefined}
        title="Confirm sensitive screening answer"
      />
      <ConfirmationDialog
        description={packageReview ? `Approve local package ${packageReview.application_id}? This records approval only; it does not submit an application to an employer.` : ""}
        onCancel={() => setApprovalConfirmationOpen(false)}
        onConfirm={() => void confirmApproval()}
        open={approvalConfirmationOpen}
        title="Confirm local package approval"
      />
      <ConfirmationDialog
        description={handoffPreview ? `Open ${handoffPreview.company}'s ${handoffPreview.title} application page at ${handoffPreview.destination_url}? This opens the employer site in a new tab. It does not upload or submit an application.` : ""}
        onCancel={() => setHandoffPreview(undefined)}
        onConfirm={() => void confirmBrowserHandoff()}
        open={handoffPreview !== undefined}
        title="Confirm browser handoff"
      />
    </section>
  );
}

interface PackageDetailsProps {
  answers: Record<string, string>;
  approvalBlocked: boolean;
  browserHandoff?: BrowserHandoff;
  onAnswerChange: (question: string, answer: string) => void;
  onApprove: () => void;
  onStartBrowserHandoff: () => void;
  onReviewAnswer: (question: string) => void;
  onExport?: () => void;
  packageReview: ApplicationPackage;
  pendingAction?: "approve" | "handoff" | "handoff_preview" | "load" | "resolve";
}

function PackageDetails({
  answers,
  approvalBlocked,
  browserHandoff,
  onAnswerChange,
  onApprove,
  onStartBrowserHandoff,
  onReviewAnswer,
  onExport,
  packageReview,
  pendingAction
}: PackageDetailsProps) {
  const isApproved = packageReview.status === "approved";
  return (
    <div className="application-details">
      <section aria-labelledby="package-status-title">
        <h3 id="package-status-title">Package status: {packageReview.status}</h3>
        {isApproved ? <p className="approved-notice">Approved locally. Submission is unavailable in this widget.</p> : null}
        {packageReview.status === "submitted" ? <p>This widget cannot submit an application or represent submission status.</p> : null}
      </section>
      <section aria-labelledby="resume-title">
        <h3 id="resume-title">Tailored resume</h3>
        <pre className="document-preview">{packageReview.tailored_resume_markdown}</pre>
        {onExport ? <button disabled={pendingAction !== undefined} onClick={onExport} type="button">Download DOCX resume</button> : null}
      </section>
      <section aria-labelledby="cover-letter-title">
        <h3 id="cover-letter-title">Cover letter</h3>
        <pre className="document-preview">{packageReview.cover_letter}</pre>
      </section>
      <section aria-labelledby="warnings-title">
        <h3 id="warnings-title">Factual warnings</h3>
        {packageReview.factual_warnings.length ? <ul>{packageReview.factual_warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul> : <p>None recorded.</p>}
      </section>
      <section aria-labelledby="screening-title">
        <h3 id="screening-title">Sensitive screening questions</h3>
        {packageReview.unresolved_screening_questions.length ? (
          <ul className="screening-list">
            {packageReview.unresolved_screening_questions.map((item) => {
              const answer = answers[item.question] ?? "";
              return (
                <li key={item.question}>
                  <p><strong>{item.category}</strong>: {item.reason}</p>
                  <p>{item.question}</p>
                  <label htmlFor={`answer-${item.question}`}>Your answer</label>
                  <textarea
                    id={`answer-${item.question}`}
                    maxLength={5_000}
                    onChange={(event) => onAnswerChange(item.question, event.target.value)}
                    value={answer}
                  />
                  <button
                    disabled={pendingAction !== undefined || answer.trim().length === 0}
                    onClick={() => onReviewAnswer(item.question)}
                    type="button"
                  >
                    Review sensitive answer
                  </button>
                </li>
              );
            })}
          </ul>
        ) : <p>No unresolved screening questions.</p>}
      </section>
      <section aria-labelledby="approval-title" className="approval-panel">
        <h3 id="approval-title">Local package approval</h3>
        {approvalBlocked && !isApproved ? <p>Approval is unavailable until all required direct-input questions are resolved.</p> : null}
        <button
          className="approval-button"
          disabled={approvalBlocked || pendingAction !== undefined}
          onClick={onApprove}
          type="button"
        >
          Approve locally (not submit)
        </button>
        {isApproved ? (
          <div>
            <h3>Employer browser handoff</h3>
            <p>Open the validated employer page yourself. This does not upload or submit your application.</p>
            <button
              disabled={pendingAction !== undefined}
              onClick={onStartBrowserHandoff}
              type="button"
            >
              Prepare employer-page handoff
            </button>
            {browserHandoff ? (
              <p>
                <a
                  href={browserHandoff.destination_url}
                  referrerPolicy="no-referrer"
                  rel="noopener noreferrer"
                  target="_blank"
                >
                  Open employer application (opens new tab)
                </a>
              </p>
            ) : null}
          </div>
        ) : null}
      </section>
    </div>
  );
}
