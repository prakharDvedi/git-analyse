const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const WS_URL = API_URL.replace("http://", "ws://").replace("https://", "wss://");

export type Finding = {
  file: string;
  reason: string;
  evidence_snippet: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
};

export type Dimension = {
  score: number;
  findings: Finding[];
  flagged_files: string[];
  recommendations?: string[];
};

export type FinalReport = {
  overall_score: number;
  summary: string;
  top_3_fixes: string[];
  files_analyzed: number;
  dimensions: {
    structure: Dimension;
    security: Dimension;
    quality: Dimension;
    testing: Dimension;
  };
};

export type AnalysisSummary = {
  id: number;
  repo_url: string;
  status: string;
  error_message?: string | null;
  created_at: string;
};

export type AnalysisDetail = AnalysisSummary & {
  report: FinalReport | null;
};

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
      fetchApi<AnalysisDetail>("/analyze", {
        method: "POST",
        body: JSON.stringify({ repo_url: repoUrl }),
      }),

    get: (analysisId: string | number) =>
      fetchApi<AnalysisDetail>(`/analyze/${analysisId}`),

    list: () => fetchApi<AnalysisSummary[]>("/analyze"),

    stream: (
      repoUrl: string,
      handlers: {
        onToken: (tokenChunk: string) => void;
        onDone: () => void;
        onError: (message: string) => void;
        onStatus?: (message: string) => void;
      }
    ) => {
      const ws = new WebSocket(`${WS_URL}/analyze/ws`);

      ws.onopen = () => {
        ws.send(JSON.stringify({ repo_url: repoUrl }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "token") handlers.onToken(msg.data ?? "");
          else if (msg.type === "done") handlers.onDone();
          else if (msg.type === "error") handlers.onError(msg.message ?? "Streaming failed");
          else if (msg.type === "status" && handlers.onStatus) handlers.onStatus(msg.message ?? "");
        } catch {
          handlers.onError("Invalid WebSocket payload");
        }
      };

      ws.onerror = () => handlers.onError("WebSocket error");
      return ws;
    },
  },
};
