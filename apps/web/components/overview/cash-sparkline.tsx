'use client';

import { useQuery } from '@tanstack/react-query';
import { getLatestForecast } from '@/lib/api-client';

export function CashSparkline() {
  const { data, isLoading, error } = useQuery({ queryKey: ['forecast-latest'], queryFn: getLatestForecast });

  if (isLoading) return <div className="flex h-40 items-center justify-center text-sm text-foreground/60">Loading projection...</div>;
  if (error) return <div className="flex h-40 items-center justify-center text-sm text-foreground/60">Forecast data is unavailable.</div>;
  return <div className="flex h-40 items-center justify-center border border-dashed border-border px-6 text-center text-sm text-foreground/60">Forecast snapshot received. The 13-week series is awaiting its finalized JSON shape.</div>;
}
