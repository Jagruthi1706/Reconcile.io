import { PageContainer } from '@/components/shell/page-container';
import Link from 'next/link';
import { ArrowRight, Database, GitCompareArrows, ShieldCheck, Sparkles } from 'lucide-react';

export default function PitchPage() {
  return (
    <PageContainer>
      <div className="mx-auto max-w-5xl py-12 lg:py-20">
        <div className="max-w-3xl">
          <p className="label-accent mb-4">Reconcile.io / Finance operations</p>
          <h1 className="heading-editorial text-4xl leading-tight text-foreground sm:text-6xl">
            Finance operations, explained with receipts.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-foreground/70">
            Reconcile bank feeds, GL entries, and settlement activity against one auditable truth model.
            Deterministic engines make the financial decisions; the Copilot explains the evidence.
          </p>
          <Link href="/razorpay" className="mt-8 inline-flex items-center gap-2 rounded-control bg-ink px-4 py-2.5 text-sm font-medium text-parchment hover:bg-ink/85 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2">
            Launch live console <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>

        <div className="mt-16 border-y border-border py-8">
          <p className="label-accent mb-5">The documented control path</p>
          <div className="grid gap-4 md:grid-cols-4">
            {[
              [Database, 'Ingest', 'Raw source payloads retained'],
              [GitCompareArrows, 'Reconcile', 'Deterministic matching tiers'],
              [ShieldCheck, 'Audit', 'Every state change traceable'],
              [Sparkles, 'Explain', 'Retrieved facts, cited clearly'],
            ].map(([Icon, title, description]) => (
              <div key={title as string} className="border-l-2 border-ink/20 pl-4">
                <Icon className="mb-3 h-5 w-5 text-foreground/70" aria-hidden="true" />
                <h2 className="text-sm font-medium text-foreground">{title as string}</h2>
                <p className="mt-1 text-sm text-foreground/60">{description as string}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
