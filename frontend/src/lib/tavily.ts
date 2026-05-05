import { tavily } from "@tavily/core";

const COMPLIANCE_DOMAINS = [
  "lacity.gov",
  "lacdph.lacounty.gov",
  "lacounty.gov",
  "abc.ca.gov",
  "cdtfa.ca.gov",
  "dir.ca.gov",
  "cslb.ca.gov",
  "cdph.ca.gov",
  "irs.gov",
  "sba.gov",
  "ladbs.org",
  "planning.lacity.org",
  "business.lacity.gov",
  "fire.lacity.org",
];

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
  const query = `required permits licenses ${businessType} ${topic} ${location}`;

  const raw = await client.search(query, {
    searchDepth: "advanced",
    maxResults: 5,
    includeAnswer: true,
    includeDomains: COMPLIANCE_DOMAINS,
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
