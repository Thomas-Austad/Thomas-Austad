import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { App } from "../src/App";

describe("App", () => {
  it("supports keyboard-reachable section navigation", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("tab", { name: "Jobs" }));

    expect(screen.getByRole("tab", { name: "Jobs" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Search and job-review views");
  });

  it("focuses and dismisses the confirmation pattern without an API action", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Preview confirmation pattern" }));

    expect(screen.getByRole("dialog")).toHaveTextContent("does not perform an API call");
    expect(document.activeElement).toHaveTextContent("Confirm");
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
