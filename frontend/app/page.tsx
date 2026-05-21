"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setLoading(true);
    setError("");

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push("/auth");
        return;
      }

      const analysis = await api.analyze.create(repoUrl);
      router.push(`/report/${analysis.id}`);
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
            Sign in to run analysis
          </Link>
        </div>
      </div>
    </main>
  );
}
