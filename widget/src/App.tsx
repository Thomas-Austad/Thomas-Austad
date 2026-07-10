import { useState } from "react";

import { ConfirmationDialog } from "./components/ConfirmationDialog";
import { StatusPanel } from "./components/StatusPanel";
import type { Route, StatusKind } from "./contracts";

const navigation: Array<{ label: string; route: Route }> = [
  { route: "profile", label: "Profile" },
  { route: "jobs", label: "Jobs" },
  { route: "applications", label: "Applications" }
];

const routeCopy: Record<Route, string> = {
  profile: "Review your evidence-grounded profile before using it downstream.",
  jobs: "Search and job-review views will be added without exposing provider credentials.",
  applications: "Prepared applications remain distinct from approval and submission."
};

export function App() {
  const [route, setRoute] = useState<Route>("profile");
  const [status, setStatus] = useState<StatusKind>("ready");
  const [confirmationOpen, setConfirmationOpen] = useState(false);

  return (
    <main className="widget-shell">
      <header>
        <p className="eyebrow">Talent Advisor</p>
        <h1>Career workspace</h1>
        <p>Private local review workspace. No application is submitted from this widget.</p>
      </header>
      <nav aria-label="Career workspace sections" className="section-nav" role="tablist">
        {navigation.map((item) => (
          <button
            aria-controls={`${item.route}-panel`}
            aria-selected={route === item.route}
            id={`${item.route}-tab`}
            key={item.route}
            onClick={() => setRoute(item.route)}
            role="tab"
            type="button"
          >
            {item.label}
          </button>
        ))}
      </nav>
      <StatusPanel detail="" kind={status} />
      <section aria-labelledby={`${route}-tab`} id={`${route}-panel`} role="tabpanel" tabIndex={-1}>
        <h2>{navigation.find((item) => item.route === route)?.label}</h2>
        <p>{routeCopy[route]}</p>
        <div className="shell-actions">
          <button onClick={() => setStatus("loading")} type="button">
            Show loading state
          </button>
          <button onClick={() => setStatus("empty")} type="button">
            Show empty state
          </button>
          <button onClick={() => setStatus("error")} type="button">
            Show error state
          </button>
          <button onClick={() => setStatus("ready")} type="button">
            Clear status
          </button>
        </div>
        <button className="confirmation-pattern" onClick={() => setConfirmationOpen(true)} type="button">
          Preview confirmation pattern
        </button>
      </section>
      <ConfirmationDialog
        description="This shell preview does not perform an API call or approve an application."
        onCancel={() => setConfirmationOpen(false)}
        onConfirm={() => setConfirmationOpen(false)}
        open={confirmationOpen}
        title="Confirm local review"
      />
    </main>
  );
}
