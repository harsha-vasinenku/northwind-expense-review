interface CitationBadgeProps {
  docIds: string[];
}

export function CitationBadge({ docIds }: CitationBadgeProps) {
  if (docIds.length === 0) return null;

  return (
    <div className="flex gap-1 flex-wrap shrink-0">
      {docIds.map((id) => (
        <span
          key={id}
          className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-mono font-medium"
          aria-label={`Policy ${id}`}
        >
          {id}
        </span>
      ))}
    </div>
  );
}
