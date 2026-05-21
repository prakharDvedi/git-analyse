"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AnalysisDetail, FinalReport, Finding, api } from "@/lib/api";

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const analysisId = params?.id;
    if (!analysisId) {
      setError("Missing analysis id.");
      setLoading(false);
      return;
    }

    api.analyze
      .get(analysisId)
      .then((result) => {
        if (!result.report) {
          setError("Analysis exists but report payload is empty.");
          return;
        }
        setAnalysis(result);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Could not load analysis.");
      })
      .finally(() => setLoading(false));
  }, [params]);

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-3xl px-6 py-24 text-slate-600">Loading report...</div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-50">
        <div className="mx-auto max-w-3xl px-6 py-24">
          <p className="rounded-md border border-red-200 bg-red-50 p-4 text-red-700">{error}</p>
          <Link href="/dashboard" className="mt-6 inline-block text-sm text-slate-900 hover:underline">
            Back to analysis history
          </Link>
        </div>
      </main>
    );
  }

  if (!analysis?.report) {
    return null;
  }

  const report = analysis.report;

  const sections: Array<{ key: keyof FinalReport["dimensions"]; label: string }> = [
    { key: "structure", label: "Structure" },
    { key: "security", label: "Security" },
    { key: "quality", label: "Quality" },
    { key: "testing", label: "Testing" },
  ];

  const severityClass: Record<Finding["severity"], string> = {
    low: "bg-slate-100 text-slate-700",
    medium: "bg-amber-100 text-amber-800",
    high: "bg-orange-100 text-orange-800",
    critical: "bg-red-100 text-red-800",
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-4xl px-6 py-10">
        <header className="mb-8">
          <div className="text-sm text-slate-500">Repo</div>
          <h1 className="text-xl font-semibold text-slate-900">{analysis.repo_url}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {analysis.status} · {new Date(analysis.created_at).toLocaleString()}
          </p>
          <p className="mt-2 text-slate-700">{report.summary}</p>
        </header>

        <section className="mb-8 rounded-md border border-slate-200 bg-white p-5">
          <div className="text-sm text-slate-500">Overall Score</div>
          <div className="mt-1 text-4xl font-semibold text-slate-900">{report.overall_score}/100</div>
          <div className="mt-1 text-sm text-slate-600">Files analyzed: {report.files_analyzed}</div>
        </section>

        <section className="mb-8 grid gap-4 md:grid-cols-2">
          {sections.map((section) => {
            const dimension = report.dimensions[section.key];
            return (
              <article key={section.key} className="rounded-md border border-slate-200 bg-white p-5">
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-semibold text-slate-900">{section.label}</h2>
                  <span className="text-sm font-medium text-slate-700">{dimension.score}/100</span>
                </div>
                <div className="mt-3 space-y-3 text-sm text-slate-700">
                  {dimension.findings?.length ? (
                    dimension.findings.slice(0, 5).map((finding, index) => (
                      <div key={index} className="rounded-md border border-slate-200 bg-slate-50 p-3">
                        <div className="flex items-center justify-between gap-3">
                          <code className="text-xs text-slate-700">{finding.file}</code>
                          <span
                            className={`rounded px-2 py-0.5 text-xs font-medium ${severityClass[finding.severity]}`}
                          >
                            {finding.severity}
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-slate-900">{finding.reason}</p>
                        <pre className="mt-2 overflow-x-auto rounded bg-white p-2 text-xs text-slate-600 whitespace-pre-wrap">
                          {finding.evidence_snippet}
                        </pre>
                        <div className="mt-2 text-xs text-slate-500">
                          Confidence: {Math.round(finding.confidence * 100)}%
                        </div>
                      </div>
                    ))
                  ) : (
                    <div>No findings returned.</div>
                  )}
                </div>
                {dimension.recommendations?.length ? (
                  <div className="mt-4">
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Recommendations
                    </h3>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                      {dimension.recommendations.slice(0, 3).map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </article>
            );
          })}
        </section>

        <section className="rounded-md border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">Top 3 Fixes</h2>
          <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-slate-700">
            {report.top_3_fixes?.length ? (
              report.top_3_fixes.map((item, index) => <li key={index}>{item}</li>)
            ) : (
              <li>No priority fixes generated.</li>
            )}
          </ol>
        </section>
      </div>
    </main>
  );
}
