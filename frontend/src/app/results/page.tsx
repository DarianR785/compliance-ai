"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/layout/Navbar";
import StatusBadge from "@/components/ui/StatusBadge";
import CategoryChip from "@/components/ui/CategoryChip";
import type { AnalyzeResponse, ChecklistItem } from "@/lib/types";

type Category = "all" | "permits" | "licenses" | "inspections" | "zoning";
const CATEGORIES: Category[] = ["all", "permits", "licenses", "inspections", "zoning"];
const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };
const STORAGE_KEY = "compliance_checked_items";

function getCheckedKey(resultId: string) {
  return `${STORAGE_KEY}_${resultId}`;
}

export default function ResultsPage() {
  const router = useRouter();
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [resultId, setResultId] = useState("");
  const [activeCategory, setActiveCategory] = useState<Category>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("compliance_result");
    if (!raw) { router.push("/check"); return; }
    try {
      const parsed: AnalyzeResponse = JSON.parse(raw);
      // Stable ID from business type + location
      const nameSlug = parsed.business_name ? `_${parsed.business_name}` : "";
      const id = `${parsed.business_type}${nameSlug}_${parsed.location}`.replace(/\s+/g, "_").toLowerCase();
      setResult(parsed);
      setResultId(id);
      // Load persisted checked state
      const savedChecked = localStorage.getItem(getCheckedKey(id));
      if (savedChecked) setChecked(new Set(JSON.parse(savedChecked)));
    } catch { router.push("/check"); }
  }, [router]);

  function toggleChecked(itemId: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) next.delete(itemId);
      else next.add(itemId);
      // Persist to localStorage so it survives page refresh
      localStorage.setItem(getCheckedKey(resultId), JSON.stringify([...next]));
      return next;
    });
  }

  if (!result) return null;

  const sorted = [...result.checklist].sort(
    (a, b) => (PRIORITY_ORDER[a.priority] ?? 3) - (PRIORITY_ORDER[b.priority] ?? 3)
  );
  const filtered = activeCategory === "all"
    ? sorted
    : sorted.filter((i) => i.category === activeCategory);

  const doneCount = checked.size;
  const totalCount = result.checklist.length;
  const progressPct = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  const statusCounts = {
    required:  result.checklist.filter((i) => i.status === "required" && !checked.has(i.id)).length,
    pending:   result.checklist.filter((i) => i.status === "pending"  && !checked.has(i.id)).length,
    compliant: result.checklist.filter((i) => i.status === "compliant").length + doneCount,
  };

  function handleSave() {
    const existing: SavedProfile[] = JSON.parse(localStorage.getItem("compliance_profiles") || "[]");
    const matchIndex = existing.findIndex(
      (p) =>
        p.businessType === result!.business_type &&
        p.location === result!.location &&
        (p.businessName || "") === (result!.business_name || "")
    );
    const profile: SavedProfile = {
      id: matchIndex >= 0 ? existing[matchIndex].id : `profile-${Date.now()}`,
      businessName: result!.business_name,
      businessType: result!.business_type,
      businessLabel: result!.business_label,
      location: result!.location,
      savedAt: new Date().toISOString().split("T")[0],
      itemCounts: statusCounts,
      data: result!,
    };
    const updated =
      matchIndex >= 0
        ? existing.map((p, i) => (i === matchIndex ? profile : p))
        : [profile, ...existing].slice(0, 10);
    localStorage.setItem("compliance_profiles", JSON.stringify(updated));
    setSaved(true);
  }

  return (
    <div className="relative z-10 flex flex-col min-h-screen">
      <Navbar />

      {result.mock && (
        <div className="bg-[var(--pending)]/10 border-b border-[var(--pending)]/30 px-6 py-2 no-print">
          <p className="mono-label text-[10px] text-[var(--pending)] text-center">
            [DEMO DATA] — FastAPI backend not connected. Start with: <code>uvicorn app:app --reload</code>
          </p>
        </div>
      )}

      <div className="flex-1 max-w-7xl mx-auto w-full px-6 py-10">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
          <div>
            <p className="mono-label text-[var(--emerald)] text-xs mb-1">COMPLIANCE CHECKLIST</p>
            <h1 className="display-heading text-xl text-[var(--paper)]">
              {result.business_name ? (
                <>
                  {result.business_name}
                  <span className="text-[var(--faint)]"> · </span>
                  <span className="text-[var(--mute-text)] text-base">{result.business_label}</span>
                </>
              ) : result.business_label}
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

          {/* Status counts */}
          <div className="flex gap-5 shrink-0">
            {(["required", "pending", "compliant"] as const).map((s) => (
              <div key={s} className="text-center">
                <p className="display-heading text-xl" style={{
                  color: s === "required" ? "var(--required)" : s === "pending" ? "var(--pending)" : "var(--compliant)"
                }}>
                  {statusCounts[s]}
                </p>
                <p className="mono-label text-[9px] text-[var(--faint)]">{s}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-1.5">
            <span className="mono-label text-[10px] text-[var(--faint)]">PROGRESS</span>
            <span className="mono-label text-[10px] text-[var(--emerald)]">
              {doneCount}/{totalCount} completed · {progressPct}%
            </span>
          </div>
          <div className="h-1 bg-[var(--steel)] w-full">
            <div
              className="h-1 bg-[var(--emerald)] transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          {/* Left: Checklist */}
          <div>
            <div className="flex flex-wrap gap-2 mb-5">
              {CATEGORIES.map((c) => (
                <CategoryChip
                  key={c}
                  category={c}
                  active={activeCategory === c}
                  onClick={() => setActiveCategory(c)}
                />
              ))}
            </div>

            <div className="space-y-px">
              {filtered.length === 0 && (
                <p className="text-[var(--faint)] text-sm py-8 text-center mono-label">
                  No items in this category.
                </p>
              )}
              {filtered.map((item: ChecklistItem) => {
                const isChecked = checked.has(item.id);
                const isExpanded = expandedId === item.id;
                return (
                  <div
                    key={item.id}
                    className="bg-[var(--midnight)] border-b border-[var(--steel)]"
                    style={{ opacity: isChecked ? 0.5 : 1, transition: "opacity 0.2s" }}
                  >
                    <div className="flex items-start gap-3 px-4 py-4">
                      {/* Checkbox */}
                      <button
                        onClick={() => toggleChecked(item.id)}
                        aria-label={isChecked ? "Mark incomplete" : "Mark complete"}
                        className="mt-0.5 shrink-0 w-5 h-5 border flex items-center justify-center transition-colors"
                        style={{
                          borderColor: isChecked ? "var(--emerald)" : "var(--steel)",
                          background: isChecked ? "var(--emerald)" : "transparent",
                        }}
                      >
                        {isChecked && (
                          <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                            <path d="M1 4L3.5 6.5L9 1" stroke="var(--void)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        )}
                      </button>

                      {/* Status + content */}
                      <button
                        className="flex-1 text-left flex items-start gap-3 min-w-0"
                        onClick={() => setExpandedId(isExpanded ? null : item.id)}
                      >
                        <StatusBadge status={item.status} />
                        <div className="flex-1 min-w-0">
                          <p
                            className="text-sm text-[var(--paper)] leading-snug"
                            style={{ textDecoration: isChecked ? "line-through" : "none" }}
                          >
                            {item.title}
                          </p>
                          {item.agency && (
                            <p className="mono-label text-[10px] text-[var(--faint)] mt-0.5">{item.agency}</p>
                          )}
                        </div>
                        <span className="mono-label text-[10px] text-[var(--faint)] shrink-0 mt-0.5">
                          {isExpanded ? "▲" : "▼"}
                        </span>
                      </button>
                    </div>

                    {isExpanded && (
                      <div className="px-5 pb-5 border-t border-[var(--steel)] bg-[var(--navy)]">
                        {item.detail && (
                          <p className="text-sm text-[var(--mute-text)] leading-relaxed mt-4 mb-4">
                            {item.detail}
                          </p>
                        )}
                        <div className="grid grid-cols-3 gap-4">
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
                        <button
                          onClick={() => toggleChecked(item.id)}
                          className="mt-4 mono-label text-[10px] px-4 py-1.5 border transition-colors"
                          style={{
                            borderColor: isChecked ? "var(--emerald)" : "var(--steel)",
                            color: isChecked ? "var(--emerald)" : "var(--faint)",
                          }}
                        >
                          {isChecked ? "[✓ MARK INCOMPLETE]" : "[MARK COMPLETE]"}
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Summary + Sources + Actions */}
          <div className="space-y-4">
            {result.description && (
              <div className="bg-[var(--midnight)] border border-[var(--steel)] p-5">
                <p className="mono-label text-[10px] text-[var(--faint)] mb-3">DESCRIPTION</p>
                <p className="text-sm text-[var(--mute-text)] leading-relaxed line-clamp-4">{result.description}</p>
              </div>
            )}
            {result.summary && (
              <div className="bg-[var(--midnight)] border border-[var(--steel)] p-5">
                <p className="mono-label text-[10px] text-[var(--emerald)] mb-3">[AI_SUMMARY]</p>
                <p className="text-sm text-[var(--mute-text)] leading-relaxed">{result.summary}</p>
              </div>
            )}

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
