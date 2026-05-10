"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface Report {
  overall_score: number;
  files_analyzed: number;
  dimensions: {
    structure: { score: number; findings: string[]; flagged_files: string[] };
    security: { score: number; findings: string[]; flagged_files: string[] };
    quality: { score: number; findings: string[]; flagged_files: string[] };
    testing: { score: number; findings: string[]; flagged_files: string[] };
  };
  summary: string;
}

export default function Report({ params }: { params: { id: string } }) {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    const id = parseInt(params.id);
    if (isNaN(id)) {
      setError("Invalid analysis ID");
      setLoading(false);
      return;
    }

    api.analyze
      .get(id)
      .then((data) => {
        if (data.report) {
          setReport(data.report as Report);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-600">Loading...</div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-red-600">{error || "Report not found"}</div>
      </div>
    );
  }

  const dimensions = [
    { key: "structure", label: "Architecture", color: "bg-blue-500" },
    { key: "security", label: "Security", color: "bg-red-500" },
    { key: "quality", label: "Quality", color: "bg-green-500" },
    { key: "testing", label: "Testing", color: "bg-yellow-500" },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <a href="/" className="text-lg font-semibold text-slate-900">
            CodeReviewer
          </a>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="mb-8">
          <div className="text-3xl font-semibold text-slate-900 mb-2">
            {report.overall_score}/100
          </div>
          <p className="text-slate-600">{report.summary}</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {dimensions.map((dim) => {
            const d = report.dimensions[dim.key as keyof typeof report.dimensions] as { score: number };
            return (
              <div key={dim.key} className="p-4 bg-white rounded-md border border-slate-200">
                <div className={`w-2 h-2 rounded-full ${dim.color} mb-2`} />
                <div className="text-2xl font-semibold text-slate-900">{d.score}</div>
                <div className="text-sm text-slate-600">{dim.label}</div>
              </div>
            );
          })}
        </div>

        <div className="space-y-6">
          {dimensions.map((dim) => {
            const d = report.dimensions[dim.key as keyof typeof report.dimensions] as { findings: string[]; flagged_files: string[] };
            if (!d.findings?.length) return null;
            return (
              <div key={dim.key} className="p-4 bg-white rounded-md border border-slate-200">
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-2 h-2 rounded-full ${dim.color}`} />
                  <h3 className="font-medium text-slate-900">{dim.label}</h3>
                </div>
                <ul className="space-y-1">
                  {d.findings.map((f, i) => (
                    <li key={i} className="text-sm text-slate-600">
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}