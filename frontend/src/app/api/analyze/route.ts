import { NextRequest, NextResponse } from "next/server";
import { MOCK_RESPONSE } from "@/lib/mock-data";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const description: string = body.description ?? "";
  const business_type: string = body.business_type ?? "";
  const location: string = body.location ?? "";
  const business_name: string = body.business_name ?? "";

  if (!description.trim()) {
    return NextResponse.json({ error: "Description is required" }, { status: 400 });
  }

  const fastapiUrl = process.env.FASTAPI_URL ?? "http://localhost:8000";

  try {
    const upstream = await fetch(`${fastapiUrl}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description, business_type, location, business_name }),
    });

    if (!upstream.ok) throw new Error(`FastAPI returned ${upstream.status}`);
    const data = await upstream.json();
    return NextResponse.json(data);
  } catch (e) {
    console.error("[analyze route] FastAPI unreachable:", e);
    return NextResponse.json({ ...MOCK_RESPONSE, mock: true });
  }
}
