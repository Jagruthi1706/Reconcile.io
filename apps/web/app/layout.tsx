import './globals.css';
import type { Metadata } from 'next';
import { AppShell } from '@/components/shell/app-shell';
import { QueryProvider } from '@/components/providers/query-provider';
import { TooltipProvider } from '@/components/ui/tooltip';

export const metadata: Metadata = {
  title: 'Reconcile.io — AI Finance Controller',
  description: 'Deterministic reconciliation, tax classification, cash forecasting, and audit trail for finance operations.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <TooltipProvider delayDuration={300}>
            <AppShell>{children}</AppShell>
          </TooltipProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
