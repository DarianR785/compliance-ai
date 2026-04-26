import type { AnalyzeResponse } from "./types";

export async function analyzeCompliance(description: string): Promise<AnalyzeResponse> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  });
  if (!res.ok) throw new Error("Analysis failed");
  return res.json();
}
