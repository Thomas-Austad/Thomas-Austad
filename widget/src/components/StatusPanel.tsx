import type { StatusKind } from "../contracts";

interface StatusPanelProps {
  detail: string;
  kind: StatusKind;
}

export function StatusPanel({ detail, kind }: StatusPanelProps) {
  if (kind === "ready") {
    return null;
  }
  const role = kind === "error" ? "alert" : "status";
  const label = kind === "loading" ? "Loading" : kind === "empty" ? "Nothing to show" : "Action needed";
  return (
    <section aria-live="polite" className={`status-panel status-${kind}`} role={role}>
      <strong>{label}</strong>
      <p>{detail}</p>
    </section>
  );
}
