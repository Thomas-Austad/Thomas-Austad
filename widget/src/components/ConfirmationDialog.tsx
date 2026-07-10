import { useEffect, useRef } from "react";

interface ConfirmationDialogProps {
  description: string;
  onCancel: () => void;
  onConfirm: () => void;
  open: boolean;
  title: string;
}

export function ConfirmationDialog({
  description,
  onCancel,
  onConfirm,
  open,
  title
}: ConfirmationDialogProps) {
  const confirmButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      confirmButton.current?.focus();
    }
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div aria-labelledby="confirmation-title" aria-modal="true" className="dialog-backdrop" role="dialog">
      <section className="dialog-panel">
        <h2 id="confirmation-title">{title}</h2>
        <p>{description}</p>
        <div className="dialog-actions">
          <button onClick={onCancel} type="button">
            Cancel
          </button>
          <button className="primary" onClick={onConfirm} ref={confirmButton} type="button">
            Confirm
          </button>
        </div>
      </section>
    </div>
  );
}
