"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Dimension = {
  score: number;
  findings: string[];
  flagged_files: string[];
};

type FinalReport = {
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

type AnalysisPayload = {
  id: number;
  repo_url: string;
  status: string;
  report: FinalReport;
};

export default function ReportPage() {
  const [analysis, setAnalysis] = useState<AnalysisPayload | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const raw = localStorage.getItem("last_analysis");
    if (!raw) {
      setError("No analysis result found. Run an analysis from the home page.");
      return;
    }

    try {
      const parsed = JSON.parse(raw) as AnalysisPayload;
      if (!parsed.report) {
        setError("Analysis exists but report payload is empty.");
        return;
      }
      setAnalysis(parsed);
    } catch {
      setError("Could not parse analysis result.");
    }
  }, []);

  if (error) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-3xl px-6 py-24">
          <p className="rounded-md border border-red-200 bg-red-50 p-4 text-red-700">{error}</p>
          <Link href="/" className="mt-6 inline-block text-sm text-slate-900 hover:underline">
            Back to home
          </Link>
        </div>
      </main>
    );
  }

  if (!analysis) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-3xl px-6 py-24 text-slate-600">Loading report...</div>
      </main>
    );
  }

  const report = analysis.report;

  const sections: Array<{ key: keyof FinalReport["dimensions"]; label: string }> = [
    { key: "structure", label: "Structure" },
    { key: "security", label: "Security" },
    { key: "quality", label: "Quality" },
    { key: "testing", label: "Testing" },
  ];

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-4xl px-6 py-10">
        <header className="mb-8">
          <div className="text-sm text-slate-500">Repo</div>
          <h1 className="text-xl font-semibold text-slate-900">{analysis.repo_url}</h1>
          <p className="mt-2 text-slate-700">{report.summary}</p>
        </header>

        <section className="mb-8 rounded-md border border-slate-200 bg-white p-5">
          <div className="text-sm text-slate-500">Overall Score</div>
          <div className="mt-1 text-4xl font-semibold text-slate-900">{report.overall_score}/100</div>
          <div className="mt-1 text-sm text-slate-600">Files analyzed: {report.files_analyzed}</div>
        </section>

        <section className="mb-8 grid gap-4 md:grid-cols-2">
          {sections.map((s) => {
            const d = report.dimensions[s.key];
            return (
              <article key={s.key} className="rounded-md border border-slate-200 bg-white p-5">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-semibold text-slate-900">{s.label}</h2>
                  <span className="text-sm font-medium text-slate-700">{d.score}/100</span>
                </div>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {d.findings?.length ? (
                    d.findings.slice(0, 5).map((f, i) => <li key={i}>{f}</li>)
                  ) : (
                    <li>No findings returned.</li>
                  )}
                </ul>
              </article>
            );
          })}
        </section>

        <section className="rounded-md border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">Top 3 Fixes</h2>
          <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-slate-700">
            {report.top_3_fixes?.length ? (
              report.top_3_fixes.map((item, i) => <li key={i}>{item}</li>)
            ) : (
              <li>No priority fixes generated.</li>
            )}
          </ol>
        </section>
      </div>
    </main>
  );
}

