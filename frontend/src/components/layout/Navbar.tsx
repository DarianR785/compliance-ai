"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/check", label: "New Check" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--steel)] bg-[var(--void)]/90 backdrop-blur-sm no-print">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="mono-label text-[var(--emerald)] hover:opacity-80 transition-opacity">
          [COMPLIANCE_CHECK]
        </Link>
        <nav className="flex items-center gap-6">
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`mono-label text-xs transition-colors ${
                pathname === href
                  ? "text-[var(--emerald)]"
                  : "text-[var(--mute-text)] hover:text-[var(--paper)]"
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
