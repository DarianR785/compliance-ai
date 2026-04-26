"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/layout/Navbar";
import { analyzeCompliance } from "@/lib/api";

const BUSINESS_TYPES = [
  { id: "restaurant", label: "Restaurant / Café", hint: "Dine-in food service" },
  { id: "food_truck", label: "Food Truck", hint: "Mobile food vending" },
  { id: "salon", label: "Salon / Barbershop", hint: "Hair, nails, beauty" },
  { id: "retail", label: "Retail Store", hint: "Goods sold to consumers" },
  { id: "contractor", label: "Contractor", hint: "Construction & trades" },
  { id: "bakery", label: "Bakery / Pastry", hint: "Baked goods" },
  { id: "bar", label: "Bar / Lounge", hint: "Alcohol-focused venue" },
];

const LA_NEIGHBORHOODS = [
  "Arts District", "Atwater Village", "Boyle Heights", "Brentwood",
  "Burbank", "Chinatown", "Culver City", "Downtown LA (DTLA)",
  "Eagle Rock", "Echo Park", "El Segundo", "Glendale",
  "Highland Park", "Hollywood", "Inglewood", "Koreatown",
  "Little Tokyo", "Long Beach", "Los Feliz", "Manhattan Beach",
  "Mar Vista", "Pasadena", "Redondo Beach", "Santa Monica",
  "Silver Lake", "Torrance", "Venice", "West Hollywood",
  "Westwood", "Other",
];

const LOADING_STEPS = [
  "[EXTRACTING ENTITIES...]",
  "[QUERYING KNOWLEDGE GRAPH...]",
  "[RETRIEVING REGULATIONS...]",
  "[GENERATING CHECKLIST...]",
];

export default function CheckPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [businessType, setBusinessType] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState("");

  async function handleSubmit() {
    setLoading(true);
    setError("");

    // Cycle loading step labels
    let i = 0;
    const interval = setInterval(() => {
      i = Math.min(i + 1, LOADING_STEPS.length - 1);
      setLoadingStep(i);
    }, 1800);

    const fullDescription = [
      businessName && `Business name: ${businessName}.`,
      description,
      businessType && `Business type: ${businessType}.`,
      location && `Location: ${location}, Los Angeles.`,
    ]
      .filter(Boolean)
      .join(" ");

    try {
      const result = await analyzeCompliance(fullDescription);
      sessionStorage.setItem("compliance_result", JSON.stringify(result));
      router.push("/results");
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center gap-6">
          <div className="w-8 h-8 border-2 border-[var(--emerald)] border-t-transparent rounded-full animate-spin" />
          <p className="mono-label text-[var(--emerald)] text-sm">
            {LOADING_STEPS[loadingStep]}
          </p>
          <p className="text-[var(--faint)] text-xs mono-label">
            Running NLP pipeline — this may take a moment
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative z-10 flex flex-col min-h-screen">
      <Navbar />

      <div className="flex-1 max-w-3xl mx-auto w-full px-6 py-12">
        {/* Header */}
        <div className="mb-10">
          <p className="mono-label text-[var(--emerald)] text-xs mb-2">
            COMPLIANCE CHECK
          </p>
          <h1 className="display-heading text-2xl text-[var(--paper)]">
            Describe Your Business
          </h1>
          <p className="text-[var(--mute-text)] text-sm mt-2">
            Step {step} of 3
          </p>
          {/* Progress bar */}
          <div className="flex gap-1 mt-4">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className="h-0.5 flex-1 transition-colors"
                style={{ background: s <= step ? "var(--emerald)" : "var(--steel)" }}
              />
            ))}
          </div>
        </div>

        {/* Step 1: Business Type */}
        {step === 1 && (
          <div>
            <p className="mono-label text-[var(--mute-text)] text-xs mb-6">
              SELECT BUSINESS TYPE
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-px bg-[var(--steel)]">
              {BUSINESS_TYPES.map(({ id, label, hint }) => (
                <button
                  key={id}
                  onClick={() => setBusinessType(id)}
                  className="bg-[var(--midnight)] p-5 text-left transition-colors hover:bg-[var(--navy)]"
                  style={{
                    borderBottom: businessType === id
                      ? "2px solid var(--emerald)"
                      : "2px solid transparent",
                  }}
                >
                  <p className="display-heading text-sm text-[var(--paper)] mb-1">{label}</p>
                  <p className="text-xs text-[var(--faint)]">{hint}</p>
                </button>
              ))}
            </div>
            <div className="mt-8 flex justify-end">
              <button
                onClick={() => setStep(2)}
                disabled={!businessType}
                className="mono-label px-6 py-2.5 bg-[var(--emerald)] text-[var(--void)] disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[var(--emerald)]/90 transition-colors text-sm"
              >
                [NEXT →]
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Description */}
        {step === 2 && (
          <div>
            <p className="mono-label text-[var(--mute-text)] text-xs mb-6">
              DESCRIBE YOUR BUSINESS
            </p>
            <div className="mb-6">
              <label className="mono-label text-xs text-[var(--faint)] mb-2 block">
                BUSINESS NAME (OPTIONAL)
              </label>
              <input
                type="text"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="e.g. Seoul Kitchen"
                className="w-full bg-[var(--midnight)] border border-[var(--steel)] px-4 py-3 text-sm text-[var(--paper)] placeholder-[var(--faint)] focus:border-[var(--emerald)] focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label className="mono-label text-xs text-[var(--faint)] mb-2 block">
                BUSINESS DESCRIPTION
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={6}
                placeholder={`e.g. "I'm opening a Korean BBQ restaurant with a full bar and rooftop patio. We'll have about 80 seats and are planning some renovation to the space."`}
                className="w-full bg-[var(--midnight)] border border-[var(--steel)] px-4 py-3 text-sm text-[var(--paper)] placeholder-[var(--faint)] focus:border-[var(--emerald)] focus:outline-none transition-colors resize-none"
              />
              <p className="text-xs text-[var(--faint)] mt-1 text-right mono-label">
                {description.length} chars
              </p>
              <p className="text-xs text-[var(--faint)] mt-2">
                Mention features like alcohol service, patio seating, live entertainment, home-based, or construction plans.
              </p>
            </div>
            <div className="mt-8 flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="mono-label px-6 py-2.5 border border-[var(--steel)] text-[var(--mute-text)] hover:border-[var(--emerald)] hover:text-[var(--emerald)] transition-colors text-sm"
              >
                [← BACK]
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={description.trim().length < 10}
                className="mono-label px-6 py-2.5 bg-[var(--emerald)] text-[var(--void)] disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[var(--emerald)]/90 transition-colors text-sm"
              >
                [NEXT →]
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Location + Confirm */}
        {step === 3 && (
          <div>
            <p className="mono-label text-[var(--mute-text)] text-xs mb-6">
              LOCATION
            </p>
            <div className="mb-8">
              <label className="mono-label text-xs text-[var(--faint)] mb-2 block">
                LA NEIGHBORHOOD
              </label>
              <select
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full bg-[var(--midnight)] border border-[var(--steel)] px-4 py-3 text-sm text-[var(--paper)] focus:border-[var(--emerald)] focus:outline-none transition-colors"
              >
                <option value="">Select a neighborhood…</option>
                {LA_NEIGHBORHOODS.map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>

            {/* Summary */}
            <div className="border border-[var(--steel)] bg-[var(--midnight)] p-6 mb-8">
              <p className="mono-label text-xs text-[var(--faint)] mb-4">REVIEW</p>
              <div className="space-y-2 text-sm">
                {businessName && (
                  <div className="flex gap-4">
                    <span className="mono-label text-[10px] text-[var(--faint)] w-28 flex-shrink-0 pt-0.5">BUSINESS</span>
                    <span className="text-[var(--paper)]">{businessName}</span>
                  </div>
                )}
                <div className="flex gap-4">
                  <span className="mono-label text-[10px] text-[var(--faint)] w-28 flex-shrink-0 pt-0.5">TYPE</span>
                  <span className="text-[var(--paper)]">{BUSINESS_TYPES.find(b => b.id === businessType)?.label}</span>
                </div>
                <div className="flex gap-4">
                  <span className="mono-label text-[10px] text-[var(--faint)] w-28 flex-shrink-0 pt-0.5">LOCATION</span>
                  <span className="text-[var(--paper)]">{location || "—"}</span>
                </div>
                <div className="flex gap-4">
                  <span className="mono-label text-[10px] text-[var(--faint)] w-28 flex-shrink-0 pt-0.5">DESCRIPTION</span>
                  <span className="text-[var(--mute-text)] leading-relaxed line-clamp-3">{description}</span>
                </div>
              </div>
            </div>

            {error && (
              <p className="text-[var(--required)] text-sm mono-label mb-4">{error}</p>
            )}

            <div className="flex justify-between">
              <button
                onClick={() => setStep(2)}
                className="mono-label px-6 py-2.5 border border-[var(--steel)] text-[var(--mute-text)] hover:border-[var(--emerald)] hover:text-[var(--emerald)] transition-colors text-sm"
              >
                [← BACK]
              </button>
              <button
                onClick={handleSubmit}
                disabled={!location}
                className="mono-label px-8 py-2.5 bg-[var(--emerald)] text-[var(--void)] disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[var(--emerald)]/90 transition-colors text-sm"
              >
                [GENERATE CHECKLIST →]
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
