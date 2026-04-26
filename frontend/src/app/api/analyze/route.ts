import { NextRequest, NextResponse } from "next/server";
import { MOCK_RESPONSE } from "@/lib/mock-data";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const description: string = body.description ?? "";

  if (!description.trim()) {
    return NextResponse.json({ error: "Description is required" }, { status: 400 });
  }

  const fastapiUrl = process.env.FASTAPI_URL ?? "http://localhost:8000";

  try {
    const upstream = await fetch(`${fastapiUrl}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description }),
      signal: AbortSignal.timeout(30000),
    });

    if (!upstream.ok) throw new Error(`FastAPI returned ${upstream.status}`);
    const data = await upstream.json();
    return NextResponse.json(data);
  } catch {
    // FastAPI unreachable — return frontend mock so the demo always works
    return NextResponse.json({ ...MOCK_RESPONSE, mock: true });
  }
}
