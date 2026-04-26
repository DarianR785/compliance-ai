"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/layout/Navbar";
import StatusBadge from "@/components/ui/StatusBadge";
import CategoryChip from "@/components/ui/CategoryChip";
import type { AnalyzeResponse, ChecklistItem } from "@/lib/types";
import { MOCK_PROFILES } from "@/lib/mock-data";

type Category = "all" | "permits" | "licenses" | "inspections" | "zoning";

const CATEGORIES: Category[] = ["all", "permits", "licenses", "inspections", "zoning"];

const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [activeCategory, setActiveCategory] = useState<Category>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("compliance_result");
    if (!raw) { router.push("/check"); return; }
    try { setResult(JSON.parse(raw)); } catch { router.push("/check"); }
  }, [router]);

  if (!result) return null;

  const sorted = [...result.checklist].sort(
    (a, b) => (PRIORITY_ORDER[a.priority] ?? 3) - (PRIORITY_ORDER[b.priority] ?? 3)
  );
  const filtered = activeCategory === "all"
    ? sorted
    : sorted.filter((i) => i.category === activeCategory);

  const counts = {
    required:  result.checklist.filter((i) => i.status === "required").length,
    pending:   result.checklist.filter((i) => i.status === "pending").length,
    compliant: result.checklist.filter((i) => i.status === "compliant").length,
  };

  function handleSave() {
    const existing = JSON.parse(localStorage.getItem("compliance_profiles") || "[]");
    const profile = {
      id: `profile-${Date.now()}`,
      businessName: result!.business_label,
      businessType: result!.business_type,
      businessLabel: result!.business_label,
      location: result!.location,
      savedAt: new Date().toISOString().split("T")[0],
      itemCounts: counts,
      data: result,
    };
    localStorage.setItem(
      "compliance_profiles",
      JSON.stringify([profile, ...existing].slice(0, 10))
    );
    setSaved(true);
  }

  return (
    <div className="relative z-10 flex flex-col min-h-screen">
      <Navbar />

      {/* Mock banner */}
      {result.mock && (
        <div className="bg-[var(--pending)]/10 border-b border-[var(--pending)]/30 px-6 py-2 no-print">
          <p className="mono-label text-[10px] text-[var(--pending)] text-center">
            [DEMO DATA] — FastAPI backend not connected. Showing sample restaurant checklist.
          </p>
        </div>
      )}

      <div className="flex-1 max-w-6xl mx-auto w-full px-6 py-10">
        {/* Header row */}
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-8">
          <div>
            <p className="mono-label text-[var(--emerald)] text-xs mb-1">COMPLIANCE CHECKLIST</p>
            <h1 className="display-heading text-xl text-[var(--paper)]">
              {result.business_label}
              <span className="text-[var(--faint)]"> · </span>
              <span className="text-[var(--mute-text)] text-base">{result.location}</span>
            </h1>
            {result.features.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {result.features.map((f) => (
                  <span key={f} className="mono-label text-[10px] px-2 py-0.5 border border-[var(--steel)] text-[var(--faint)]">
                    {f.replace("_", " ")}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Status summary */}
          <div className="flex gap-4 shrink-0">
            {(["required", "pending", "compliant"] as const).map((s) => (
              <div key={s} className="text-center">
                <p className="display-heading text-xl" style={{
                  color: s === "required" ? "var(--required)" : s === "pending" ? "var(--pending)" : "var(--compliant)"
                }}>
                  {counts[s]}
                </p>
                <p className="mono-label text-[9px] text-[var(--faint)]">{s}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          {/* Left: Checklist */}
          <div>
            {/* Category filter */}
            <div className="flex flex-wrap gap-2 mb-6">
              {CATEGORIES.map((c) => (
                <CategoryChip
                  key={c}
                  category={c}
                  active={activeCategory === c}
                  onClick={() => setActiveCategory(c)}
                />
              ))}
            </div>

            {/* Items */}
            <div className="space-y-px">
              {filtered.length === 0 && (
                <p className="text-[var(--faint)] text-sm py-8 text-center mono-label">
                  No items in this category.
                </p>
              )}
              {filtered.map((item: ChecklistItem) => (
                <div key={item.id} className="bg-[var(--midnight)] border-b border-[var(--steel)]">
                  <button
                    className="w-full text-left px-5 py-4 flex items-start gap-4 hover:bg-[var(--navy)] transition-colors"
                    onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                  >
                    <StatusBadge status={item.status} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-[var(--paper)] leading-snug">{item.title}</p>
                      {item.agency && (
                        <p className="mono-label text-[10px] text-[var(--faint)] mt-0.5">{item.agency}</p>
                      )}
                    </div>
                    <span className="mono-label text-[10px] text-[var(--faint)] shrink-0 mt-0.5">
                      {expandedId === item.id ? "▲" : "▼"}
                    </span>
                  </button>

                  {expandedId === item.id && (
                    <div className="px-5 pb-5 border-t border-[var(--steel)] bg-[var(--navy)]">
                      {item.detail && (
                        <p className="text-sm text-[var(--mute-text)] leading-relaxed mt-4 mb-4">
                          {item.detail}
                        </p>
                      )}
                      <div className="grid grid-cols-3 gap-4 mt-3">
                        {item.fee && (
                          <div>
                            <p className="mono-label text-[9px] text-[var(--faint)] mb-1">FEE</p>
                            <p className="text-xs text-[var(--paper)]">{item.fee}</p>
                          </div>
                        )}
                        {item.timeline && (
                          <div>
                            <p className="mono-label text-[9px] text-[var(--faint)] mb-1">TIMELINE</p>
                            <p className="text-xs text-[var(--paper)]">{item.timeline}</p>
                          </div>
                        )}
                        {item.renewal && (
                          <div>
                            <p className="mono-label text-[9px] text-[var(--faint)] mb-1">RENEWAL</p>
                            <p className="text-xs text-[var(--paper)]">{item.renewal}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Right: Summary + Sources */}
          <div className="space-y-4">
            {/* AI Summary */}
            {result.summary && (
              <div className="bg-[var(--midnight)] border border-[var(--steel)] p-5">
                <p className="mono-label text-[10px] text-[var(--emerald)] mb-3">[AI_SUMMARY]</p>
                <p className="text-sm text-[var(--mute-text)] leading-relaxed">{result.summary}</p>
              </div>
            )}

            {/* Sources */}
            {result.sources.length > 0 && (
              <div className="bg-[var(--midnight)] border border-[var(--steel)] p-5">
                <p className="mono-label text-[10px] text-[var(--faint)] mb-3">SOURCES</p>
                <div className="space-y-3">
                  {result.sources.map((src, i) => (
                    <div key={i} className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-xs text-[var(--paper)] leading-snug">{src.title}</p>
                        <p className="mono-label text-[9px] text-[var(--faint)] mt-0.5">{src.agency}</p>
                      </div>
                      <span className="mono-label text-[10px] text-[var(--emerald)] shrink-0">
                        {Math.round(src.score * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2 no-print">
              <button
                onClick={handleSave}
                disabled={saved}
                className="w-full mono-label text-xs py-2.5 border border-[var(--steel)] text-[var(--mute-text)] hover:border-[var(--emerald)] hover:text-[var(--emerald)] transition-colors disabled:opacity-50"
              >
                {saved ? "[✓ SAVED TO DASHBOARD]" : "[SAVE TO DASHBOARD]"}
              </button>
              <button
                onClick={() => window.print()}
                className="w-full mono-label text-xs py-2.5 border border-[var(--steel)] text-[var(--mute-text)] hover:border-[var(--trace)] hover:text-[var(--trace)] transition-colors"
              >
                [EXPORT PDF]
              </button>
              <Link
                href="/check"
                className="w-full mono-label text-xs py-2.5 border border-[var(--steel)] text-[var(--faint)] hover:text-[var(--mute-text)] transition-colors block text-center"
              >
                [START OVER]
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
