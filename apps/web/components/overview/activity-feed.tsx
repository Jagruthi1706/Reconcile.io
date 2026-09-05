'use client';

import { useQuery } from '@tanstack/react-query';

import { getAudit } from '@/lib/api-client';

export function ActivityFeed() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['audit', { limit: 6 }],
    queryFn: () => getAudit({ limit: 6 }),
  });

  if (isLoading) return <p className="text-sm text-foreground/60">Loading activity...</p>;
  if (error) return <p className="text-sm text-foreground/60">Activity data is unavailable.</p>;
  if (!data?.length) return <p className="text-sm text-foreground/60">No audited activity has been recorded.</p>;

  return (
    <div className="divide-y divide-border text-sm">
      {data.map((entry) => (
        <div key={entry.id} className="flex items-baseline justify-between gap-4 py-3 first:pt-0 last:pb-0">
          <div className="min-w-0">
            <p className="truncate text-foreground">{entry.action} <span className="text-foreground/60">{entry.entity_type}</span></p>
            <p className="mt-1 text-xs text-foreground/50">{entry.actor}</p>
          </div>
          <time className="shrink-0 text-xs tabular-nums text-foreground/50" dateTime={entry.created_at}>
            {new Date(entry.created_at).toLocaleString()}
          </time>
        </div>
      ))}
    </div>
  );
}
