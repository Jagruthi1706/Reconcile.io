export function ExceptionsHeatmap() {
  return (
    <div className="flex min-h-[180px] items-center justify-center border border-dashed border-border px-6 text-center">
      <p className="max-w-sm text-sm leading-6 text-foreground/60">
        Source aggregation is unavailable in the current exception response contract. This visualization will remain empty until each exception includes its canonical source.
      </p>
    </div>
  );
}
