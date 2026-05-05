import type { TavilyResult } from "./tavily";
import type { ChecklistItem } from "./types";
import regulationsData from "../../data/regulations.json";

interface Regulation {
  id: string;
  title: string;
  agency: string;
  business_type: string | string[];
  features: string[];
  category: "permits" | "licenses" | "inspections" | "zoning";
  text: string;
  fee?: string;
  timeline?: string;
}

const PRIORITY_BY_CATEGORY: Record<string, ChecklistItem["priority"]> = {
  licenses:    "critical",
  permits:     "high",
  inspections: "high",
  zoning:      "medium",
};

function matchTavilyUrl(reg: Regulation, tavilyResults: TavilyResult[]): string {
  const regWords = new Set(
    `${reg.title} ${reg.agency}`.toLowerCase().split(/\s+/)
  );
  let bestUrl = "";
  let bestScore = 0;
  for (const r of tavilyResults) {
    const resultWords = new Set(`${r.title} ${r.content.slice(0, 200)}`.toLowerCase().split(/\s+/));
    const overlap = [...regWords].filter((w) => resultWords.has(w)).length;
    if (overlap > bestScore) {
      bestScore = overlap;
      bestUrl = r.url;
    }
  }
  return bestUrl;
}

export function getRegulations(
  businessType: string,
  features: string[],
  tavilyResults: TavilyResult[],
): ChecklistItem[] {
  const regs = (regulationsData as Regulation[]).filter((reg) => {
    const types = Array.isArray(reg.business_type) ? reg.business_type : [reg.business_type];
    if (!types.includes(businessType)) return false;
    if (reg.features.length > 0 && !reg.features.some((f) => features.includes(f))) return false;
    return true;
  });

  return regs.map((reg) => {
    const priority = PRIORITY_BY_CATEGORY[reg.category] ?? "high";
    return {
      id: reg.id,
      title: reg.title,
      status: priority === "critical" || priority === "high" ? "required" : "pending",
      priority,
      category: reg.category,
      detail: reg.text,
      agency: reg.agency,
      fee: reg.fee ?? "",
      timeline: reg.timeline ?? "",
      renewal: "",
      url: matchTavilyUrl(reg, tavilyResults),
    };
  });
}
