import { cn } from "@/lib/utils";

const KNOWN_CATEGORIES = [
  { key: "Health", emoji: "🏥" },
  { key: "Education", emoji: "📚" },
  { key: "Retail", emoji: "🛒" },
  { key: "Food", emoji: "🍽️" },
  { key: "Religious", emoji: "⛪" },
  { key: "Government", emoji: "🏛️" },
  { key: "Transport", emoji: "🚌" },
];

interface CategoryQuickFiltersProps {
  allCategories: string[];
  selected: string | null;
  onSelect: (category: string | null) => void;
  t: (key: string) => string;
}

export function CategoryQuickFilters({
  allCategories,
  selected,
  onSelect,
  t,
}: CategoryQuickFiltersProps) {
  const available = KNOWN_CATEGORIES.filter((c) =>
    allCategories.some(
      (ac) => ac.toLowerCase() === c.key.toLowerCase()
    )
  );

  if (available.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1 px-3 pb-2">
      <button
        onClick={() => onSelect(null)}
        className={cn(
          "text-[10px] px-2 py-0.5 rounded-full border transition-colors",
          selected === null
            ? "bg-primary text-primary-foreground border-primary"
            : "border-border text-muted-foreground hover:bg-secondary/60"
        )}
      >
        {t("poi_manager_filter_all")}
      </button>
      {available.map((cat) => (
        <button
          key={cat.key}
          onClick={() =>
            onSelect(selected === cat.key ? null : cat.key)
          }
          className={cn(
            "text-[10px] px-2 py-0.5 rounded-full border transition-colors",
            selected === cat.key
              ? "bg-primary text-primary-foreground border-primary"
              : "border-border text-muted-foreground hover:bg-secondary/60"
          )}
        >
          {cat.emoji} {t(`poi_manager_category_${cat.key.toLowerCase()}`)}
        </button>
      ))}
    </div>
  );
}
