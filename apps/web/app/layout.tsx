import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MISTY - Artificial Cognitive System",
  description:
    "Web interface for MISTY, an LLM-independent artificial cognitive system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-neural-bg text-slate-200 antialiased">
        {children}
      </body>
    </html>
  );
}
