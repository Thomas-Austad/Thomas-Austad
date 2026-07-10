import { useState } from "react";

import { ProfileReviewView } from "./components/ProfileReviewView";
import type { Route } from "./contracts";
import type { ProfileToolClient } from "./profileClient";

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

interface AppProps {
  profileClient?: ProfileToolClient;
}

export function App({ profileClient }: AppProps) {
  const [route, setRoute] = useState<Route>("profile");

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
      <section aria-labelledby={`${route}-tab`} id={`${route}-panel`} role="tabpanel" tabIndex={-1}>
        {route === "profile" ? (
          <ProfileReviewView client={profileClient} />
        ) : (
          <>
            <h2>{navigation.find((item) => item.route === route)?.label}</h2>
            <p>{routeCopy[route]}</p>
          </>
        )}
      </section>
    </main>
  );
}
