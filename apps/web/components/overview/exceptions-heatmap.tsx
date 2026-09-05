'use client';
import { useQuery } from '@tanstack/react-query';
import { getExceptions } from '@/lib/api-client';

export function ExceptionsHeatmap() {
  const query = useQuery({ queryKey: ['exceptions'], queryFn: () => getExceptions() });

  return (
    <div className="flex min-h-[180px] items-center justify-center border border-dashed border-border px-6 text-center">
      {query.isLoading && <p className="text-sm text-foreground/60">Loading exceptions...</p>}
      {query.error && <p className="text-sm text-error">Exception data is unavailable.</p>}
      {!query.isLoading && !query.error && <p className="text-sm text-foreground/60">{query.data?.length ?? 0} exception{query.data?.length === 1 ? '' : 's'} recorded. Source breakdown is unavailable from the current contract.</p>}
    </div>
  );
}
