import { createRoot, type Root } from "react-dom/client";

import { App } from "./App";
import { AppsBridge } from "./bridge";
import type { JobToolClient } from "./jobClient";
import type { ProfileToolClient } from "./profileClient";
import "./styles.css";

const CHATGPT_HOST_ORIGIN = "https://chatgpt.com";

class TalentAdvisorWidget extends HTMLElement {
  #root: Root | undefined;
  #bridge: AppsBridge | undefined;

  connectedCallback(): void {
    if (this.#root) {
      return;
    }
    const mountPoint = document.createElement("div");
    this.appendChild(mountPoint);
    this.#root = createRoot(mountPoint);
    this.#bridge = new AppsBridge({
      allowedOrigins: [CHATGPT_HOST_ORIGIN],
      eventTarget: window,
      hostWindow: window.parent
    });
    this.#bridge.start();
    this.#root.render(
      <App
        jobClient={this.#bridge as JobToolClient}
        profileClient={this.#bridge as ProfileToolClient}
      />
    );
  }

  disconnectedCallback(): void {
    this.#bridge?.dispose();
    this.#bridge = undefined;
    this.#root?.unmount();
    this.#root = undefined;
  }
}

if (!customElements.get("talent-advisor-widget")) {
  customElements.define("talent-advisor-widget", TalentAdvisorWidget);
}
