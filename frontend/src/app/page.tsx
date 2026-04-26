import Link from "next/link";
import Navbar from "@/components/layout/Navbar";

const steps = [
  {
    num: "01",
    title: "Describe Your Business",
    body: "Enter a plain-English description — business type, location, seating capacity, and special features like outdoor dining or alcohol service.",
  },
  {
    num: "02",
    title: "AI Analyzes Requirements",
    body: "spaCy NER extracts entities, the regulatory knowledge graph maps permit dependencies, and sentence-BERT retrieves relevant regulation texts.",
  },
  {
    num: "03",
    title: "Get Your Checklist",
    body: "A structured compliance checklist with required permits, estimated costs, processing timelines, and renewal schedules — all source-backed.",
  },
];

const features = [
  {
    tag: "NER",
    title: "Named Entity Recognition",
    body: "spaCy extracts business type, location, capacity, and features (liquor, outdoor dining, construction) from free-text input.",
  },
  {
    tag: "GRAPH",
    title: "Regulatory Knowledge Graph",
    body: "NetworkX directed graph encodes jurisdictions, permit types, and conditional dependencies — composite requirements are never missed.",
  },
  {
    tag: "EMBEDDINGS",
    title: "Semantic Search",
    body: "Sentence-BERT embeddings and cosine similarity retrieve the most relevant regulations from our LA regulatory corpus.",
  },
  {
    tag: "SUMMARIZER",
    title: "BART Summarization",
    body: "A BART transformer model translates dense municipal code into plain-language guidance with concrete costs and processing times.",
  },
  {
    tag: "SOURCES",
    title: "Source-Backed Results",
    body: "Grounded in real government sources: LADBS, LAFD, LACDPH, CDTFA, ABC, and the U.S. Small Business Administration.",
  },
  {
    tag: "PROFILES",
    title: "Persistent Profiles",
    body: "Save and revisit checklists as your business evolves. Track renewals and keep your compliance requirements current.",
  },
];

export default function Home() {
  return (
    <div className="relative z-10 flex flex-col min-h-screen">
      <Navbar />

      {/* Hero */}
      <section className="flex flex-col items-center justify-center text-center px-6 py-24 max-w-4xl mx-auto w-full">
        <p className="mono-label text-[var(--emerald)] mb-5 text-xs">
          AI-Powered · Los Angeles · Small Business Compliance
        </p>
        <h1 className="display-heading text-4xl md:text-[3.25rem] text-[var(--paper)] mb-6 leading-tight">
          Know Every Permit
          <br />
          <span className="text-[var(--emerald)]">Before You Open.</span>
        </h1>
        <p className="text-[var(--mute-text)] text-base md:text-lg max-w-xl mb-10 leading-relaxed">
          Describe your business in plain English. ComplianceCheck generates a
          complete, source-backed compliance checklist tailored to your business
          type and LA location.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Link
            href="/check"
            className="mono-label px-8 py-3 bg-[var(--emerald)] text-[var(--void)] hover:bg-[var(--emerald)]/90 transition-colors text-sm"
          >
            [GET STARTED →]
          </Link>
          <Link
            href="/dashboard"
            className="mono-label px-8 py-3 border border-[var(--steel)] text-[var(--mute-text)] hover:border-[var(--emerald)] hover:text-[var(--emerald)] transition-colors text-sm"
          >
            [VIEW DASHBOARD]
          </Link>
        </div>
      </section>

      <div className="border-t border-[var(--steel)]" />

      {/* How It Works */}
      <section className="py-16 px-6 max-w-6xl mx-auto w-full">
        <p className="mono-label text-[var(--faint)] text-xs mb-8">HOW IT WORKS</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[var(--steel)]">
          {steps.map(({ num, title, body }) => (
            <div key={num} className="bg-[var(--midnight)] p-8">
              <p className="display-heading text-3xl text-[var(--emerald)]/15 mb-5 select-none">
                [{num}]
              </p>
              <h3 className="display-heading text-sm text-[var(--paper)] mb-3">{title}</h3>
              <p className="text-sm text-[var(--mute-text)] leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="border-t border-[var(--steel)]" />

      {/* Core Techniques */}
      <section className="py-16 px-6 max-w-6xl mx-auto w-full">
        <p className="mono-label text-[var(--faint)] text-xs mb-8">CORE NLP TECHNIQUES</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-[var(--steel)]">
          {features.map(({ tag, title, body }) => (
            <div key={tag} className="bg-[var(--midnight)] p-6 flex flex-col gap-3">
              <span className="mono-label text-[10px] text-[var(--trace)] bg-[var(--trace)]/10 px-2 py-0.5 w-fit border border-[var(--trace)]/20">
                {tag}
              </span>
              <h3 className="display-heading text-sm text-[var(--paper)]">{title}</h3>
              <p className="text-sm text-[var(--mute-text)] leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="border-t border-[var(--steel)]" />

      {/* CTA */}
      <section className="py-16 px-6">
        <div className="max-w-xl mx-auto text-center">
          <h2 className="display-heading text-xl text-[var(--paper)] mb-3">
            Ready to check compliance?
          </h2>
          <p className="text-[var(--mute-text)] text-sm mb-8">
            Currently scoped to Los Angeles — city, county, and state requirements.
          </p>
          <Link
            href="/check"
            className="mono-label px-8 py-3 bg-[var(--emerald)] text-[var(--void)] hover:bg-[var(--emerald)]/90 transition-colors inline-block text-sm"
          >
            [START FREE CHECK →]
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--steel)] py-6 px-6 no-print mt-auto">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <span className="mono-label text-[var(--faint)] text-[10px]">
            [COMPLIANCE_CHECK] — USC TAC 459 NLP Project
          </span>
          <span className="mono-label text-[var(--faint)] text-[10px]">
            Darian · Britney · Mohamad · Urvi · Nandini · Sami · Zeina
          </span>
        </div>
      </footer>
    </div>
  );
}
