const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000";
let csrfToken: string | null = null;

export function setApiCsrfToken(token: string | null): void {
  csrfToken = token && token.trim() !== "" ? token.trim() : null;
}

async function requestJson<TResponse>(
  method: "GET" | "POST" | "PUT" | "DELETE",
  path: string,
  payload?: unknown,
  options?: { timeoutMs?: number }
): Promise<TResponse> {
  const timeoutMs = options?.timeoutMs;
  const controller = timeoutMs && timeoutMs > 0 ? new AbortController() : undefined;
  const timeoutHandle = controller
    ? setTimeout(() => {
        controller.abort();
      }, timeoutMs)
    : undefined;
  let response: Response;
  try {
    const headers: Record<string, string> = {};
    if (payload !== undefined) {
      headers["Content-Type"] = "application/json";
    }
    if (method !== "GET" && csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      credentials: "include",
      body: payload === undefined ? undefined : JSON.stringify(payload),
      signal: controller?.signal
    });
  } catch (error) {
    if (timeoutHandle !== undefined) {
      clearTimeout(timeoutHandle);
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`request timeout: ${path}`);
    }
    throw error;
  }
  if (timeoutHandle !== undefined) {
    clearTimeout(timeoutHandle);
  }

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // keep default message
    }
    throw new Error(message);
  }

  return (await response.json()) as TResponse;
}

export async function apiPost<TResponse>(
  path: string,
  payload: unknown,
  options?: { timeoutMs?: number }
): Promise<TResponse> {
  return requestJson<TResponse>("POST", path, payload, options);
}

export async function apiPut<TResponse>(
  path: string,
  payload: unknown,
  options?: { timeoutMs?: number }
): Promise<TResponse> {
  return requestJson<TResponse>("PUT", path, payload, options);
}

export async function apiDelete<TResponse>(
  path: string,
  options?: { timeoutMs?: number }
): Promise<TResponse> {
  return requestJson<TResponse>("DELETE", path, undefined, options);
}

export async function apiGet<TResponse>(path: string): Promise<TResponse> {
  return requestJson<TResponse>("GET", path);
}

export function parseManualTokens(input: string): string[] | undefined {
  const normalized = input
    .split(/[\s,\u3001]+/)
    .map((token) => token.trim())
    .filter((token) => token.length > 0);
  return normalized.length > 0 ? normalized : undefined;
}
