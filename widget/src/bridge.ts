import {
  allowedToolNameSchema,
  jsonRpcEnvelopeSchema,
  toolArgumentsSchema,
  type AllowedToolName,
  type JsonRpcEnvelope
} from "./contracts";

type MessageTarget = Pick<Window, "postMessage">;
type MessageEventTarget = Pick<Window, "addEventListener" | "removeEventListener">;

export class BridgeProtocolError extends Error {
  override name = "BridgeProtocolError";
}

export interface AppsBridgeOptions {
  eventTarget: MessageEventTarget;
  hostWindow: MessageTarget;
  allowedOrigins: readonly string[];
  requestTimeoutMs?: number;
  onToolResult?: (result: unknown) => void;
}

interface PendingRequest {
  reject: (reason: Error) => void;
  resolve: (value: unknown) => void;
  timeout: number;
}

/** A small, origin-checked bridge for the MCP Apps JSON-RPC host protocol. */
export class AppsBridge {
  readonly #allowedOrigins: ReadonlySet<string>;
  readonly #eventTarget: MessageEventTarget;
  readonly #hostWindow: MessageTarget;
  readonly #onToolResult?: (result: unknown) => void;
  readonly #pending = new Map<number, PendingRequest>();
  readonly #requestTimeoutMs: number;
  #nextRequestId = 1;
  #started = false;

  constructor(options: AppsBridgeOptions) {
    if (options.allowedOrigins.length === 0) {
      throw new BridgeProtocolError("At least one trusted host origin is required.");
    }
    this.#allowedOrigins = new Set(options.allowedOrigins);
    this.#eventTarget = options.eventTarget;
    this.#hostWindow = options.hostWindow;
    this.#onToolResult = options.onToolResult;
    this.#requestTimeoutMs = options.requestTimeoutMs ?? 10_000;
  }

  start(): void {
    if (this.#started) {
      return;
    }
    this.#started = true;
    this.#eventTarget.addEventListener("message", this.#handleMessage);
    this.#notify("ui/initialize", {});
  }

  dispose(): void {
    this.#eventTarget.removeEventListener("message", this.#handleMessage);
    for (const pending of this.#pending.values()) {
      window.clearTimeout(pending.timeout);
      pending.reject(new BridgeProtocolError("Widget bridge was disposed."));
    }
    this.#pending.clear();
    this.#started = false;
  }

  async callTool(name: AllowedToolName, args: Record<string, unknown>): Promise<unknown> {
    const validatedName = allowedToolNameSchema.parse(name);
    const validatedArguments = toolArgumentsSchema.parse(args);
    return this.#request("tools/call", { name: validatedName, arguments: validatedArguments });
  }

  #handleMessage = (event: MessageEvent<unknown>): void => {
    if (event.source !== (this.#hostWindow as unknown)) {
      return;
    }
    if (!this.#allowedOrigins.has(event.origin)) {
      return;
    }

    const parsed = jsonRpcEnvelopeSchema.safeParse(event.data);
    if (!parsed.success) {
      return;
    }
    this.#receive(parsed.data);
  };

  #receive(message: JsonRpcEnvelope): void {
    if (message.id !== undefined) {
      const pending = this.#pending.get(message.id);
      if (!pending) {
        return;
      }
      this.#pending.delete(message.id);
      window.clearTimeout(pending.timeout);
      if (message.error) {
        pending.reject(new BridgeProtocolError(message.error.message));
        return;
      }
      pending.resolve(message.result);
      return;
    }

    if (message.method === "ui/notifications/tool-result") {
      this.#onToolResult?.(message.params);
    }
  }

  #notify(method: string, params: Record<string, unknown>): void {
    this.#hostWindow.postMessage({ jsonrpc: "2.0", method, params }, this.#hostOrigin());
  }

  #request(method: string, params: Record<string, unknown>): Promise<unknown> {
    const id = this.#nextRequestId++;
    return new Promise((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        this.#pending.delete(id);
        reject(new BridgeProtocolError("Widget bridge request timed out."));
      }, this.#requestTimeoutMs);
      this.#pending.set(id, { resolve, reject, timeout });
      this.#hostWindow.postMessage({ jsonrpc: "2.0", id, method, params }, this.#hostOrigin());
    });
  }

  #hostOrigin(): string {
    const [origin] = this.#allowedOrigins;
    return origin;
  }
}
