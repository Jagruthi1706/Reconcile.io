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
  const linePoints = values.map((value, index) => {
    const x = values.length === 1 ? 50 : 4 + (index / (values.length - 1)) * 92;
    const normalized = maximum === minimum ? 0.5 : (value - minimum) / range;
    const y = 4 + (1 - normalized) * 92;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="relative flex h-40 items-end gap-1 border border-border px-4 pb-4 pt-6" aria-label="13-week projected cash series">
      <svg className="pointer-events-none absolute inset-x-4 top-6 h-[calc(100%-3.5rem)] w-[calc(100%-2rem)]" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <polyline points={linePoints} fill="none" stroke="currentColor" strokeWidth="1.5" vectorEffect="non-scaling-stroke" className="text-forecast" />
      </svg>
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
