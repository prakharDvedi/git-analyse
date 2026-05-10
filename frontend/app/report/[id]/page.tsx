"use client";

import Link from "next/link";

export default function ReportPage() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-2xl px-6 py-24 text-center">
        <h1 className="text-2xl font-semibold text-slate-900">Report View</h1>
        <p className="mt-3 text-slate-600">
          Detailed report persistence is not wired yet. Use the home page to fetch and inspect a
          repository tree.
        </p>
        <Link href="/" className="mt-6 inline-block text-sm text-slate-900 hover:underline">
          Back to home
        </Link>
      </div>
    </main>
  );
}

