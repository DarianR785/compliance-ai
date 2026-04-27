"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/check", label: "New Check" },
  { href: "/dashboard", label: "Dashboard" },
];

const NAV_STYLE: React.CSSProperties = {
  fontFamily: "var(--font-jetbrains), monospace",
  fontSize: "1.1rem",
  fontWeight: 500,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
};

function ChecklistIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <rect x="1" y="1" width="16" height="16" rx="1" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M5 6.5L7 8.5L11 4.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="13" y1="6.5" x2="13" y2="6.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="5" y1="11" x2="13" y2="11" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeOpacity="0.4"/>
      <line x1="5" y1="13.5" x2="10" y2="13.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeOpacity="0.4"/>
    </svg>
  );
}

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--steel)] bg-[var(--void)]/90 backdrop-blur-sm no-print w-full">
      <div className="w-full px-12 h-20 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2.5 text-[var(--emerald)] hover:opacity-80 transition-opacity"
        >
          <ChecklistIcon />
          <span style={{ fontFamily: "var(--font-jetbrains), monospace", fontSize: "1.75rem", fontWeight: 600, letterSpacing: "0.05em" }}>
            ComplianceCheck
          </span>
        </Link>

        <nav className="flex items-center gap-8">
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              style={{
                ...NAV_STYLE,
                color: pathname === href ? "var(--emerald)" : "var(--mute-text)",
              }}
              className="transition-colors hover:text-[var(--paper)]"
            >
              {label}
            </Link>
          ))}
          <button
            onClick={() => alert("Login coming soon")}
            style={{
              ...NAV_STYLE,
              color: "var(--mute-text)",
              padding: "0.375rem 1rem",
              border: "1px solid var(--steel)",
            }}
            className="transition-colors hover:border-[var(--emerald)] hover:text-[var(--emerald)]"
          >
            Login
          </button>
        </nav>
      </div>
    </header>
  );
}
