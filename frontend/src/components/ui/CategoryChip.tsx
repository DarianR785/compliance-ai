type Category = "permits" | "licenses" | "inspections" | "zoning" | "all";

const colors: Record<Category, string> = {
  all:         "var(--mute-text)",
  permits:     "var(--trace)",
  licenses:    "#A78BFA",
  inspections: "var(--pending)",
  zoning:      "#34D399",
};

export default function CategoryChip({
  category,
  active,
  onClick,
}: {
  category: Category;
  active?: boolean;
  onClick?: () => void;
}) {
  const color = colors[category];
  return (
    <button
      onClick={onClick}
      className="mono-label text-[10px] px-3 py-1 transition-all"
      style={{
        color: active ? "var(--void)" : color,
        background: active ? color : "transparent",
        border: `1px solid ${color}`,
        opacity: active ? 1 : 0.6,
        cursor: onClick ? "pointer" : "default",
      }}
    >
      {category}
    </button>
  );
}
