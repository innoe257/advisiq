import { clearTokens, getAccessToken, getRefreshToken, setAccessToken } from "../auth-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d: { msg?: string }) => d.msg).join(", ");
    }
  } catch {
    // response body wasn't JSON — fall through to the generic message below
  }
  return response.statusText || "Request failed";
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) return null;

  const data = await response.json();
  setAccessToken(data.access_token);
  return data.access_token as string;
}

interface RequestOptions extends RequestInit {
  /** Attach the access token and retry once via refresh on a 401. Default true. */
  auth?: boolean;
}

/**
 * Every authenticated request goes through here so token refresh is
 * handled once, centrally: a 401 triggers exactly one refresh attempt,
 * then retries the original request before giving up and redirecting
 * to /login.
 */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, headers, ...rest } = options;

  const doFetch = (token: string | null): Promise<Response> => {
    const isFormEncoded = rest.body instanceof URLSearchParams;
    const finalHeaders: HeadersInit = {
      ...(rest.body && !isFormEncoded ? { "Content-Type": "application/json" } : {}),
      ...headers,
      ...(auth && token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(`${API_URL}${path}`, { ...rest, headers: finalHeaders });
  };

  let token = auth ? getAccessToken() : null;
  let response = await doFetch(token);

  if (auth && response.status === 401) {
    token = await refreshAccessToken();
    if (token) {
      response = await doFetch(token);
    } else {
      clearTokens();
      if (typeof window !== "undefined") window.location.href = "/login";
      throw new ApiError(401, "Session expired");
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
