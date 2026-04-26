type Status = "required" | "pending" | "compliant";

const config: Record<Status, { label: string; color: string; bg: string }> = {
  required:  { label: "Required",  color: "var(--required)", bg: "rgba(239,68,68,0.1)" },
  pending:   { label: "Pending",   color: "var(--pending)",  bg: "rgba(245,158,11,0.1)" },
  compliant: { label: "Compliant", color: "var(--compliant)",bg: "rgba(16,185,129,0.1)" },
};

export default function StatusBadge({ status }: { status: Status }) {
  const { label, color, bg } = config[status];
  return (
    <span
      className="mono-label text-[10px] px-2 py-0.5 inline-flex items-center gap-1.5"
      style={{ color, background: bg, border: `1px solid ${color}30` }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{ background: color }}
      />
      {label}
    </span>
  );
}
