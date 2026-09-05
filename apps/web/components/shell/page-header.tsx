import { cn } from '@/lib/utils';

export function PageHeader({
  title,
  question,
  description,
  actions,
  className,
}: {
  title: string;
  question?: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-col gap-4 border-b border-border pb-4 md:flex-row md:items-end md:justify-between', className)}>
      <div>
        <p className="label-accent mb-2">{title}</p>
        {question && <h1 className="heading-editorial text-3xl text-foreground">{question}</h1>}
        {description && <p className="mt-2 max-w-2xl text-sm text-foreground/70">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
