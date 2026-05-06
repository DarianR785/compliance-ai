import { NextRequest, NextResponse } from "next/server";
import { searchRegulations } from "@/lib/tavily";
import { extractPermitsWithClaude } from "@/lib/gemini";
import { MOCK_RESPONSE } from "@/lib/mock-data";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const description: string = (body.description ?? "").trim();
  const business_type: string = (body.business_type ?? "").trim();
  const location: string = (body.location ?? "Los Angeles").trim();
  const business_name: string = (body.business_name ?? "").trim();

  if (!description) {
    return NextResponse.json({ error: "Description is required" }, { status: 400 });
  }

  if (!process.env.TAVILY_API_KEY || !process.env.GEMINI_API_KEY) {
    console.warn("[analyze] Missing API keys — returning mock");
    return NextResponse.json({ ...MOCK_RESPONSE, mock: true });
  }

  try {
    const tavilyResp = await searchRegulations(description, business_type, location);

    const sources = tavilyResp.results.map((r) => ({
      title: r.title,
      agency: r.sourceDomain,
      score: r.score,
      url: r.url,
    }));

    const checklist = await extractPermitsWithClaude(
      description,
      business_type,
      location,
      tavilyResp.results,
    );

    if (!checklist.length && !tavilyResp.summary) {
      return NextResponse.json({ ...MOCK_RESPONSE, mock: true });
    }

    return NextResponse.json({
      business_name,
      business_type,
      business_label: business_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      location,
      features: [],
      description,
      summary: tavilyResp.summary,
      checklist,
      sources,
      mock: false,
    });
  } catch (e) {
    console.error("[analyze] Error:", e);
    return NextResponse.json({ ...MOCK_RESPONSE, mock: true });
  }
}
