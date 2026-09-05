 'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { askCopilot, getCopilotHistory } from '@/lib/api-client';

export default function CopilotPage() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<{ answer: string; cited_record_ids: string[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const history = useQuery({ queryKey: ['copilot-history'], queryFn: getCopilotHistory });
  async function ask() { if (!question.trim()) return; setLoading(true); try { setAnswer(await askCopilot(question)); } finally { setLoading(false); } }
  return (
    <PageContainer>
      <PageHeader title="Copilot" question="Why did this happen?" description="An explanatory layer over retrieved ledger facts. It never decides matches, classifications, or forecast numbers." />
      <div className="mt-6 rounded-panel border border-border bg-card p-5"><div className="flex items-center justify-between border-b border-border pb-4"><span className="label-accent">Structured-only / Gemini-enhanced</span><span className="rounded-control border border-border px-2 py-1 text-xs text-foreground/60">Read-only</span></div><div className="min-h-56 py-6 text-sm leading-6 text-foreground/80">{answer ? <><p>{answer.answer}</p><p className="mt-4 text-xs text-foreground/50">Citations: {answer.cited_record_ids.join(', ') || 'None'}</p></> : history.data?.[0] ? <p>{history.data[0].answer}</p> : <p className="text-foreground/60">Ask about retrieved exception records.</p>}</div><div className="flex gap-2 border-t border-border pt-4"><input value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void ask(); }} placeholder="Ask about a reconciled record..." aria-label="Copilot question" className="h-10 flex-1 rounded-control border border-border bg-background px-3 text-sm" /><button disabled={loading} onClick={() => void ask()} type="button" className="rounded-control bg-ink px-4 text-sm text-parchment">{loading ? 'Asking...' : 'Ask'}</button></div></div>
    </PageContainer>
  );
}
