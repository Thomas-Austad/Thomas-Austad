import { describe, expect, it, vi } from "vitest";

import { AppsBridge } from "../src/bridge";

function makeBridge() {
  const eventTarget = new EventTarget();
  const hostWindow = { postMessage: vi.fn() };
  const bridge = new AppsBridge({
    allowedOrigins: ["https://trusted.example"],
    eventTarget: eventTarget as unknown as Window,
    hostWindow: hostWindow as unknown as Window,
    requestTimeoutMs: 500
  });
  return { bridge, eventTarget, hostWindow };
}

describe("AppsBridge", () => {
  it("sends only to the configured trusted origin", () => {
    const { bridge, hostWindow } = makeBridge();

    bridge.start();

    expect(hostWindow.postMessage).toHaveBeenCalledWith(
      { jsonrpc: "2.0", method: "ui/initialize", params: {} },
      "https://trusted.example"
    );
  });

  it("ignores responses from an untrusted origin", async () => {
    const { bridge, eventTarget, hostWindow } = makeBridge();
    bridge.start();
    const result = bridge.callTool("review_candidate_profile", { candidate_id: "candidate-1" });
    const request = hostWindow.postMessage.mock.calls.at(-1)?.[0] as { id: number };

    eventTarget.dispatchEvent(
      new MessageEvent("message", {
        data: { id: request.id, jsonrpc: "2.0", result: { candidate_id: "candidate-1" } },
        origin: "https://untrusted.example",
        source: hostWindow as unknown as MessageEventSource
      })
    );

    expect(hostWindow.postMessage).toHaveBeenCalledTimes(2);
    eventTarget.dispatchEvent(
      new MessageEvent("message", {
        data: { id: request.id, jsonrpc: "2.0", result: { candidate_id: "candidate-1" } },
        origin: "https://trusted.example",
        source: hostWindow as unknown as MessageEventSource
      })
    );

    await expect(result).resolves.toEqual({ candidate_id: "candidate-1" });
  });

  it("rejects tool names outside the allowlist", async () => {
    const { bridge } = makeBridge();

    await expect(bridge.callTool("approve_application" as never, {})).rejects.toThrow();
  });
});
