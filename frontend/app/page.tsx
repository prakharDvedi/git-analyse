"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{
    owner: string;
    repo: string;
    total_discovered: number;
    total_returned: number;
    truncated: boolean;
    files: Array<{ path: string; size?: number }>;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const tree = await api.review.tree(repoUrl);
      setResult({
        ...tree,
        files: tree.files.map((f) => ({ path: f.path, size: f.size })),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="max-w-2xl mx-auto px-6 py-24">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-semibold text-slate-900 mb-3">
            CodeReviewer
          </h1>
          <p className="text-lg text-slate-600">
            Paste a GitHub repo. Get a structured engineering review.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            placeholder="https://github.com/owner/repo"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            error={error}
          />

          <Button type="submit" className="w-full" loading={loading}>
            Analyze Repository
          </Button>
        </form>

        <div className="mt-8 text-center">
          <Link href="/auth" className="text-sm text-slate-600 hover:text-slate-900">
            Sign in for protected routes
          </Link>
        </div>

        {result && (
          <section className="mt-10 rounded-md border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-slate-900">
              {result.owner}/{result.repo}
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Found {result.total_discovered} files, returned {result.total_returned}
              {result.truncated ? " (truncated to 50)." : "."}
            </p>
            <ul className="mt-4 max-h-72 space-y-1 overflow-auto text-sm text-slate-700">
              {result.files.slice(0, 25).map((f) => (
                <li key={f.path}>{f.path}</li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
