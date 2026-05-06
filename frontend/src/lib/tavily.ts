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

export async function searchRegulations(
  topic: string,
  businessType: string,
  location: string,
): Promise<TavilyResponse> {
  const apiKey = process.env.TAVILY_API_KEY;
  if (!apiKey) throw new Error("TAVILY_API_KEY not set");

  const client = tavily({ apiKey });
  // Include full description so retrieval targets the specific business (e.g. alcohol, outdoor, live music)
  const query = `required permits licenses regulations ${businessType} Los Angeles ${location} ${topic}`;

  const raw = await client.search(query, {
    searchDepth: "advanced",
    maxResults: 10,
    includeAnswer: true,
  });

  const results: TavilyResult[] = (raw.results ?? []).map((r) => ({
    title: r.title ?? "",
    url: r.url ?? "",
    content: r.content ?? "",
    score: r.score ?? 0,
    sourceDomain: (() => {
      try { return new URL(r.url ?? "").hostname.replace("www.", ""); }
      catch { return r.url ?? ""; }
    })(),
  }));

  return {
    query,
    summary: (raw as { answer?: string }).answer ?? "",
    results,
  };
}
