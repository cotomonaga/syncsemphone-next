const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

export async function apiPost<TResponse>(
  path: string,
  payload: unknown
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
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
