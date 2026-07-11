import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApplicationReviewView } from "../src/components/ApplicationReviewView";
import type { ApplicationToolClient } from "../src/applicationClient";
import type { ApplicationPackage } from "../src/contracts";

const question = "Are you authorized to work in the United States?";
const preparedPackage: ApplicationPackage = {
  application_id: "application-123",
  candidate_id: "candidate-1",
  job_id: "job-1",
  tailored_resume_markdown: "# Avery Example\nPlatform engineer",
  cover_letter: "I am interested in this role.",
  factual_warnings: ["Confirm work authorization directly."],
  requires_user_input: [question],
  unresolved_screening_questions: [{
    question,
    category: "work_authorization",
    reason: "Work authorization answers require direct user confirmation."
  }],
  confirmed_screening_answers: [],
  status: "prepared"
};

const resolvedPackage: ApplicationPackage = {
  ...preparedPackage,
  requires_user_input: [],
  unresolved_screening_questions: [],
  confirmed_screening_answers: [{
    question,
    category: "work_authorization",
    confirmed_at: "2026-07-10T00:00:00Z"
  }]
};

function makeClient(): ApplicationToolClient {
  return {
    callTool: vi.fn().mockImplementation((name: string) => {
      if (name === "get_application_review") {
        return Promise.resolve(preparedPackage);
      }
      if (name === "resolve_application_screening_answer") {
        return Promise.resolve(resolvedPackage);
      }
      return Promise.resolve({ ...resolvedPackage, status: "approved" });
    })
  };
}

describe("ApplicationReviewView", () => {
  it("uses a newly prepared package immediately without another tool call", async () => {
    const client: ApplicationToolClient = { callTool: vi.fn() };
    render(<ApplicationReviewView client={client} preparedPackage={preparedPackage} />);

    expect(await screen.findByText("Tailored resume")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Package status: prepared" })).toBeInTheDocument();
    expect(client.callTool).not.toHaveBeenCalled();
  });

  it("requires direct confirmations for a sensitive answer and local approval without offering submission", async () => {
    const user = userEvent.setup();
    const client = makeClient();
    render(<ApplicationReviewView client={client} />);

    await user.type(screen.getByLabelText("Application package ID"), "application-123");
    await user.click(screen.getByRole("button", { name: "Load prepared package" }));

    expect(await screen.findByText("Tailored resume")).toBeInTheDocument();
    expect(screen.getByText("Confirm work authorization directly.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve locally (not submit)" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /^submit/i })).not.toBeInTheDocument();

    await user.type(screen.getByLabelText("Your answer"), "Yes");
    await user.click(screen.getByRole("button", { name: "Review sensitive answer" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("does not submit an application");
    expect(client.callTool).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    expect(client.callTool).toHaveBeenLastCalledWith("resolve_application_screening_answer", expect.objectContaining({
      application_id: "application-123",
      question,
      answer: "Yes",
      confirmed_by_user: true,
      idempotency_key: expect.any(String)
    }));

    expect(await screen.findByText("No unresolved screening questions.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Approve locally (not submit)" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("records approval only");
    expect(client.callTool).toHaveBeenCalledTimes(2);
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    expect(client.callTool).toHaveBeenLastCalledWith("approve_prepared_application_review", expect.objectContaining({
      application_id: "application-123",
      confirmed_by_user: true,
      idempotency_key: expect.any(String)
    }));
    expect(await screen.findByText("Approved locally. Submission is unavailable in this widget.")).toBeInTheDocument();
  });

  it("prevents repeat activation while approval is pending", async () => {
    const user = userEvent.setup();
    let resolveApproval: (value: unknown) => void = () => undefined;
    const client: ApplicationToolClient = {
      callTool: vi.fn().mockImplementation((name: string) => {
        if (name === "get_application_review") {
          return Promise.resolve(resolvedPackage);
        }
        return new Promise((resolve) => { resolveApproval = resolve; });
      })
    };
    render(<ApplicationReviewView client={client} />);

    await user.type(screen.getByLabelText("Application package ID"), "application-123");
    await user.click(screen.getByRole("button", { name: "Load prepared package" }));
    await screen.findByRole("button", { name: "Approve locally (not submit)" });
    await user.click(screen.getByRole("button", { name: "Approve locally (not submit)" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(screen.getByRole("button", { name: "Approve locally (not submit)" })).toBeDisabled();
    expect(client.callTool).toHaveBeenCalledTimes(2);
    resolveApproval({ ...resolvedPackage, status: "approved" });
    expect(await screen.findByText("Approved locally. Submission is unavailable in this widget.")).toBeInTheDocument();
  });

  it("shows a safe error for a malformed approval response without claiming approval", async () => {
    const user = userEvent.setup();
    const client: ApplicationToolClient = {
      callTool: vi.fn().mockResolvedValueOnce(resolvedPackage).mockResolvedValueOnce({ status: "approved" })
    };
    render(<ApplicationReviewView client={client} />);

    await user.type(screen.getByLabelText("Application package ID"), "application-123");
    await user.click(screen.getByRole("button", { name: "Load prepared package" }));
    await user.click(await screen.findByRole("button", { name: "Approve locally (not submit)" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("could not be approved");
    expect(screen.queryByText("Approved locally. Submission is unavailable in this widget.")).not.toBeInTheDocument();
  });
});
