const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

export async function apiPost<TResponse>(
  path: string,
  payload: unknown,
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
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload),
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

export async function apiGet<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json"
    }
  });

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

export function parseManualTokens(input: string): string[] | undefined {
  const normalized = input
    .split(/[\s,\u3001]+/)
    .map((token) => token.trim())
    .filter((token) => token.length > 0);
  return normalized.length > 0 ? normalized : undefined;
}
