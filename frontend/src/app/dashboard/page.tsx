"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/layout/Navbar";
import type { SavedProfile } from "@/lib/types";
import { MOCK_PROFILES } from "@/lib/mock-data";

const TYPE_LABELS: Record<string, string> = {
  restaurant: "Restaurant",
  food_truck: "Food Truck",
  salon: "Salon",
  retail: "Retail",
  contractor: "Contractor",
  bakery: "Bakery",
  bar: "Bar",
};

export default function DashboardPage() {
  const router = useRouter();
  const [profiles, setProfiles] = useState<SavedProfile[]>([]);

  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem("compliance_profiles") || "[]");
    // Merge user-saved with mocks so the page is never empty
    const merged = [...saved, ...MOCK_PROFILES].reduce<SavedProfile[]>((acc, p) => {
      if (!acc.find((x) => x.id === p.id)) acc.push(p);
      return acc;
    }, []);
    setProfiles(merged);
  }, []);

  function loadProfile(profile: SavedProfile) {
    sessionStorage.setItem("compliance_result", JSON.stringify(profile.data));
    router.push("/results");
  }

  function deleteProfile(id: string) {
    const saved = JSON.parse(localStorage.getItem("compliance_profiles") || "[]");
    const updated = (saved as SavedProfile[]).filter((p) => p.id !== id);
    localStorage.setItem("compliance_profiles", JSON.stringify(updated));
    setProfiles((prev) => prev.filter((p) => p.id !== id || MOCK_PROFILES.find((m) => m.id === id)));
  }

  return (
    <div className="relative z-10 flex flex-col min-h-screen">
      <Navbar />

      <div className="flex-1 max-w-6xl mx-auto w-full px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="mono-label text-[var(--emerald)] text-xs mb-1">DASHBOARD</p>
            <h1 className="display-heading text-xl text-[var(--paper)]">Saved Profiles</h1>
          </div>
          <Link
            href="/check"
            className="mono-label text-xs px-5 py-2.5 bg-[var(--emerald)] text-[var(--void)] hover:bg-[var(--emerald)]/90 transition-colors"
          >
            [+ NEW CHECK]
          </Link>
        </div>

        {profiles.length === 0 ? (
          <div className="text-center py-24 border border-[var(--steel)] bg-[var(--midnight)]">
            <p className="mono-label text-[var(--faint)] text-xs mb-4">NO PROFILES YET</p>
            <Link href="/check" className="mono-label text-xs text-[var(--emerald)] hover:underline">
              Run your first compliance check →
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-[var(--steel)]">
            {profiles.map((profile) => (
              <div key={profile.id} className="bg-[var(--midnight)] p-6 flex flex-col gap-4">
                {/* Top */}
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="display-heading text-sm text-[var(--paper)] truncate">
                      {profile.businessName || profile.businessLabel}
                    </p>
                    <p className="mono-label text-[10px] text-[var(--faint)] mt-0.5">
                      {TYPE_LABELS[profile.businessType] || profile.businessType} · {profile.location}
                    </p>
                  </div>
                  <span className="mono-label text-[9px] text-[var(--faint)] shrink-0 mt-0.5">
                    {profile.savedAt}
                  </span>
                </div>

                {/* Status dots */}
                <div className="flex gap-4">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[var(--required)]" />
                    <span className="mono-label text-[10px] text-[var(--mute-text)]">
                      {profile.itemCounts.required} required
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[var(--pending)]" />
                    <span className="mono-label text-[10px] text-[var(--mute-text)]">
                      {profile.itemCounts.pending} pending
                    </span>
                  </div>
                  {profile.itemCounts.compliant > 0 && (
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[var(--compliant)]" />
                      <span className="mono-label text-[10px] text-[var(--mute-text)]">
                        {profile.itemCounts.compliant} done
                      </span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-auto pt-2 border-t border-[var(--steel)]">
                  <button
                    onClick={() => loadProfile(profile)}
                    className="flex-1 mono-label text-[10px] py-2 border border-[var(--emerald)] text-[var(--emerald)] hover:bg-[var(--emerald)] hover:text-[var(--void)] transition-colors"
                  >
                    [VIEW]
                  </button>
                  {!MOCK_PROFILES.find((m) => m.id === profile.id) && (
                    <button
                      onClick={() => deleteProfile(profile.id)}
                      className="mono-label text-[10px] px-3 py-2 border border-[var(--steel)] text-[var(--faint)] hover:border-[var(--required)] hover:text-[var(--required)] transition-colors"
                    >
                      [×]
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
