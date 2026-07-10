import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import type { ProfileToolClient } from "../src/profileClient";

const profileReview = {
  profile: {
    candidate_id: "candidate-1",
    name: "Avery Example",
    headline: "Software engineer",
    current_level: "Senior",
    primary_functions: ["Platform engineering"],
    skills: [{ name: "Python", proficiency: 0.9, years: 5 }],
    experience: [],
    education: [],
    certifications: [],
    ambiguities: ["Confirm current location."],
    generated_at: "2026-07-10T00:00:00Z"
  },
  evidence: [{
    candidate_id: "candidate-1",
    claim_type: "skill",
    claim_ref: "Python",
    source: "resume",
    text: "Built Python services.",
    confidence: 0.9,
    source_ref: "resume:1"
  }],
  corrections: []
};

function makeProfileClient(): ProfileToolClient {
  return { callTool: vi.fn().mockResolvedValue(profileReview) };
}

describe("App", () => {
  it("supports keyboard-reachable section navigation", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("tab", { name: "Jobs" }));

    expect(screen.getByRole("tab", { name: "Jobs" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Search and job-review views");
  });

  it("shows a safe error without attempting a profile request when no secure client is available", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText("Candidate ID"), "candidate-1");
    await user.click(screen.getByRole("button", { name: "Review profile" }));

    expect(screen.getByRole("alert")).toHaveTextContent("secure widget connection is unavailable");
    expect(screen.queryByText("Avery Example")).not.toBeInTheDocument();
  });

  it("reviews evidence and confirms a bounded correction before calling the tool", async () => {
    const user = userEvent.setup();
    const client = makeProfileClient();
    render(<App profileClient={client} />);

    await user.type(screen.getByLabelText("Candidate ID"), "candidate-1");
    await user.click(screen.getByRole("button", { name: "Review profile" }));

    expect(await screen.findByText("Evidence-grounded profile")).toBeInTheDocument();
    expect(screen.getByText(/Built Python services/)).toBeInTheDocument();
    expect(screen.getByText("Confirm current location.")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Corrected Headline"), "Principal software engineer");
    await user.click(screen.getByRole("button", { name: "Review correction" }));

    expect(screen.getByRole("dialog")).toHaveTextContent("Save your user-provided headline correction");
    expect(document.activeElement).toHaveTextContent("Confirm");
    expect(client.callTool).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Confirm" }));
    expect(client.callTool).toHaveBeenLastCalledWith("correct_candidate_profile", {
      candidate_id: "candidate-1",
      corrections: { headline: "Principal software engineer" },
      confirmed_by_user: true
    });
  });
});
