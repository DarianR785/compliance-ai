import type { AnalyzeResponse } from "./types";

export async function analyzeCompliance(
  description: string,
  businessType: string,
  location: string,
  businessName: string,
): Promise<AnalyzeResponse> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      description,
      business_type: businessType,
      location,
      business_name: businessName,
    }),
  });
  if (!res.ok) throw new Error("Analysis failed");
  return res.json();
}
