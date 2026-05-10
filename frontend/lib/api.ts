const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    if (Array.isArray(error.detail)) {
      const message = error.detail
        .map((d: { loc?: Array<string | number>; msg?: string }) => {
          const loc = Array.isArray(d.loc) ? d.loc.join(".") : "body";
          return `${loc}: ${d.msg ?? "Invalid value"}`;
        })
        .join(" | ");
      throw new Error(message || "Validation failed");
    }
    throw new Error(error.detail || "Request failed");
  }

  return response.json();
}

export const api = {
  auth: {
    register: (data: { email: string; username: string; password: string }) =>
      fetchApi<{ id: number; email: string }>("/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    login: (data: { email: string; password: string }) =>
      fetchApi<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }).then((res) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("token", res.access_token);
        }
        return res;
      }),

    me: () => fetchApi<{ id: number; email: string; username: string }>("/auth/me"),

    logout: () => {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
      }
    },
  },

  review: {
    tree: (repoUrl: string) =>
      fetchApi<{
        owner: string;
        repo: string;
        total_discovered: number;
        total_returned: number;
        truncated: boolean;
        files: Array<{ path: string; type: string; size?: number }>;
      }>("/review/tree", {
        method: "POST",
        body: JSON.stringify({ repo_url: repoUrl }),
      }),
  },

  analyze: {
    create: (repoUrl: string) =>
      fetchApi<{ id: number; repo_url: string; status: string; report: unknown }>("/analyze", {
        method: "POST",
        body: JSON.stringify({ repo_url: repoUrl }),
      }),
  },
};
