'use client';

import { useQuery } from '@tanstack/react-query';
import { getLatestForecast } from '@/lib/api-client';

export function CashSparkline() {
  const { data, isLoading, error } = useQuery({ queryKey: ['forecast-latest'], queryFn: getLatestForecast });

  if (isLoading) return <div className="flex h-40 items-center justify-center text-sm text-foreground/60">Loading projection...</div>;
  if (error) return <div className="flex h-40 items-center justify-center text-sm text-foreground/60">Forecast data is unavailable.</div>;
  if (!data?.weeks.length) return <div className="flex h-40 items-center justify-center border border-dashed border-border px-6 text-center text-sm text-foreground/60">No forecast weeks are available.</div>;

  const values = data.weeks.map((week) => week.projected_cash);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const range = maximum - minimum || 1;

  return (
    <div className="flex h-40 items-end gap-1 border border-border px-4 pb-4 pt-6" aria-label="13-week projected cash series">
      {data.weeks.map((week) => (
        <div key={week.week} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
          <div
            className="w-full rounded-t-sm bg-forecast"
            style={{ height: `${Math.max(8, ((week.projected_cash - minimum) / range) * 100)}%` }}
            title={`Week ${week.week}: ${week.projected_cash}`}
          />
          <span className="text-[10px] text-foreground/50">{week.week}</span>
        </div>
      ))}
    </div>
  );
}
