export function Percentage({ value, className }: { value: number; className?: string }) {
  return <span className={className}>{value.toFixed(1)}%</span>;
}
