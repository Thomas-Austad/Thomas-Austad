import { createRoot, type Root } from "react-dom/client";

import { App } from "./App";
import "./styles.css";

class TalentAdvisorWidget extends HTMLElement {
  #root: Root | undefined;

  connectedCallback(): void {
    if (this.#root) {
      return;
    }
    const mountPoint = document.createElement("div");
    this.appendChild(mountPoint);
    this.#root = createRoot(mountPoint);
    this.#root.render(<App />);
  }

  disconnectedCallback(): void {
    this.#root?.unmount();
    this.#root = undefined;
  }
}

if (!customElements.get("talent-advisor-widget")) {
  customElements.define("talent-advisor-widget", TalentAdvisorWidget);
}
