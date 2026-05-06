import { tavily } from "@tavily/core";


export interface TavilyResult {
  title: string;
  url: string;
  content: string;
  score: number;
  sourceDomain: string;
}

export interface TavilyResponse {
  query: string;
  summary: string;
  results: TavilyResult[];
}

function toHostname(url: string): string {
  try { return new URL(url).hostname.replace("www.", ""); }
  catch { return url; }
}

export async function searchRegulations(
  description: string,
  businessType: string,
  location: string,
): Promise<TavilyResponse> {
  const apiKey = process.env.TAVILY_API_KEY;
  if (!apiKey) throw new Error("TAVILY_API_KEY not set");

  const client = tavily({ apiKey });
  const loc = location || "Los Angeles";
  const type = businessType.replace(/_/g, " ");

  // Primary query: description-first so specific features (alcohol, live music, etc.) drive retrieval
  const primaryQuery = `${description} permits licenses regulations ${type} ${loc}`;

  // Secondary query: broader regulatory overview for this business type
  const secondaryQuery = `${type} business permits licenses requirements ${loc} California`;

  const searchOpts = { searchDepth: "advanced" as const, maxResults: 6, includeAnswer: true };

  const [primary, secondary] = await Promise.all([
    client.search(primaryQuery, searchOpts),
    client.search(secondaryQuery, searchOpts),
  ]);

  // Merge and deduplicate by URL, primary results ranked first
  const seen = new Set<string>();
  const merged: TavilyResult[] = [];
  for (const r of [...(primary.results ?? []), ...(secondary.results ?? [])]) {
    if (!seen.has(r.url ?? "")) {
      seen.add(r.url ?? "");
      merged.push({
        title: r.title ?? "",
        url: r.url ?? "",
        content: r.content ?? "",
        score: r.score ?? 0,
        sourceDomain: toHostname(r.url ?? ""),
      });
    }
    if (merged.length >= 10) break;
  }

  return {
    query: primaryQuery,
    summary: (primary as { answer?: string }).answer ?? "",
    results: merged,
  };
}
