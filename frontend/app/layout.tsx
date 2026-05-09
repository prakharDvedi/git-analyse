import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodeReviewer",
  description: "Paste a GitHub repo. Get a structured engineering review.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}