import { GoogleGenerativeAI } from "@google/generative-ai";
import type { TavilyResult } from "./tavily";
import type { ChecklistItem } from "./types";

const SYSTEM_PROMPT = `You are a compliance expert for Los Angeles small businesses. Given a business description and web search results about regulations, extract ALL relevant permits, licenses, inspections, and zoning requirements.

Return a JSON array of permit objects. Each object must have:
- id: unique slug (e.g. "health-permit", "abc-license")
- title: short official name
- category: one of "permits" | "licenses" | "inspections" | "zoning"
- priority: one of "critical" | "high" | "medium" | "low"
- status: "required" if critical/high, otherwise "pending"
- agency: issuing authority (e.g. "LA County Department of Public Health")
- detail: 1-2 sentence description of what this requirement entails
- fee: estimated cost if mentioned, otherwise ""
- timeline: processing time if mentioned, otherwise ""
- renewal: renewal frequency if mentioned, otherwise ""
- url: most relevant source URL from the search results, or ""

Be thorough — extract every regulatory requirement mentioned or implied by the business type and description. If the description mentions alcohol, outdoor seating, live music, employees, construction, signage, or any other specific feature, include ALL corresponding permits for those features. Do not include requirements clearly irrelevant to this business.

Return ONLY a valid JSON array with no markdown, no code fences, no explanation.`;

export async function extractPermitsWithClaude(
  description: string,
  businessType: string,
  location: string,
  tavilyResults: TavilyResult[],
): Promise<ChecklistItem[]> {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error("GEMINI_API_KEY not set");

  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({
    model: "gemini-2.5-flash",
    systemInstruction: SYSTEM_PROMPT,
  });

  const sourcesText = tavilyResults
    .map((r, i) => `[${i + 1}] ${r.title}\nURL: ${r.url}\n${r.content.slice(0, 800)}`)
    .join("\n\n---\n\n");

  const prompt = `Business Description: ${description}
Business Type: ${businessType}
Location: ${location}

Search Results from Government Sources:
${sourcesText}

Extract all relevant compliance requirements for this specific business.`;

  const result = await model.generateContent(prompt);
  const text = result.response.text();

  const cleaned = text.replace(/```json\s*/g, "").replace(/```\s*/g, "").trim();

  const parsed = JSON.parse(cleaned) as ChecklistItem[];
  return parsed.map((item, idx) => ({
    ...item,
    id: item.id || `item-${idx}`,
    status: item.status ?? (item.priority === "critical" || item.priority === "high" ? "required" : "pending"),
    fee: item.fee ?? "",
    timeline: item.timeline ?? "",
    renewal: item.renewal ?? "",
    url: item.url ?? "",
  }));
}
