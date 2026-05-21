"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnalysisSummary, api } from "@/lib/api";

export default function Dashboard() {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.analyze.list()
      .then((items) => {
        setAnalyses(items);
      })
      .catch(() => {
        window.location.href = "/auth";
      })
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    api.auth.logout();
    window.location.href = "/";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-lg font-semibold text-slate-900">
            CodeReviewer
          </Link>
          <button onClick={handleLogout} className="text-sm text-slate-600 hover:text-slate-900">
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-slate-900">Your Analyses</h1>
          <Link href="/" className="text-sm text-slate-600 hover:text-slate-900">
            + New analysis
          </Link>
        </div>

        {analyses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-slate-600 mb-4">No analyses yet</p>
            <Link href="/" className="text-sm text-slate-900 hover:underline">
              Analyze your first repo
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {analyses.map((a) => (
              <Link
                key={a.id}
                href={`/report/${a.id}`}
                className="block p-4 bg-white rounded-md border border-slate-200 hover:border-slate-300 transition-colors"
              >
                <div className="font-medium text-slate-900">{a.repo_url}</div>
                <div className="text-sm text-slate-600">
                  {a.status} · {new Date(a.created_at).toLocaleString()}
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
