'use client';

import { useState, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Play, Loader2, Check, AlertCircle } from 'lucide-react';

import { createRun, getRunDetail } from '@/lib/api-client';
import type { ReconciliationRunDetail } from '@/lib/api-types';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

const stateLabels = {
  idle: 'Run Reconciliation Now',
  starting: 'Starting…',
  running: 'Running…',
  done: 'Reconciliation Complete',
  error: 'Run Unavailable',
} as const;

const progressMessages = {
  idle: '',
  starting: 'Starting reconciliation…',
  running: 'Reconciliation running…',
  done: 'Reconciliation complete.',
  error: 'The reconciliation run could not be completed.',
} as const;

const POLL_INTERVAL = 1500;
const MAX_POLLS = 120;

type RunState = keyof typeof stateLabels;

export function RunReconciliation() {
  const [runState, setRunState] = useState<RunState>('idle');
  const [runId, setRunId] = useState<string | null>(null);
  const [runDetail, setRunDetail] = useState<ReconciliationRunDetail | null>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const pollCount = useRef(0);

  const handleRun = useCallback(async () => {
    if (runState === 'starting' || runState === 'running') return;

    setRunState('starting');
    setRunDetail(null);
    pollCount.current = 0;

    try {
      const response = await createRun();
      setRunId(response.run_id);
      setRunState('running');
      toast({ title: 'Reconciliation started', description: `Run ID: ${response.run_id.slice(0, 12)}…` });

      const poll = async () => {
        pollCount.current += 1;
        if (pollCount.current > MAX_POLLS) {
          setRunState('error');
          toast({ title: 'Reconciliation timed out', description: 'The run did not complete within the expected time.', variant: 'destructive' });
          return;
        }

        try {
          const detail = await getRunDetail(response.run_id);

          if (detail.status === 'done') {
            setRunState('done');
            setRunDetail(detail);
            toast({ title: 'Reconciliation complete', description: `${detail.records_processed} records processed · Match rate: ${detail.match_rate_count.toFixed(1)}%` });

            await queryClient.invalidateQueries({ queryKey: ['runs'] });
            await queryClient.invalidateQueries({ queryKey: ['exceptions'] });
            await queryClient.invalidateQueries({ queryKey: ['tax-classifications'] });
            await queryClient.invalidateQueries({ queryKey: ['forecast-latest'] });
            await queryClient.invalidateQueries({ queryKey: ['audit'] });
            return;
          }

          setTimeout(poll, POLL_INTERVAL);
        } catch {
          setTimeout(poll, POLL_INTERVAL);
        }
      };

      setTimeout(poll, POLL_INTERVAL);
    } catch {
      setRunState('error');
      toast({ title: 'Unable to start reconciliation', description: 'The API could not be reached.', variant: 'destructive' });
    }
  }, [runState, queryClient, toast]);

  const isBusy = runState === 'starting' || runState === 'running';

  return (
    <div className="flex items-center gap-3">
      <Button
        onClick={handleRun}
        disabled={isBusy}
        size="sm"
        className={runState === 'done' ? 'bg-success text-success-foreground hover:bg-success/90' : runState === 'error' ? 'bg-error text-error-foreground hover:bg-error/90' : ''}
      >
        {isBusy && <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />}
        {runState === 'done' && <Check className="h-3.5 w-3.5" aria-hidden="true" />}
        {runState === 'error' && <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />}
        {runState === 'idle' && <Play className="h-3.5 w-3.5" aria-hidden="true" />}
        {stateLabels[runState]}
      </Button>

      <span className="sr-only" aria-live="polite" aria-atomic="true">
        {progressMessages[runState]}
        {runDetail && ` ${runDetail.records_processed} records processed. Match rate: ${runDetail.match_rate_count.toFixed(1)} percent.`}
      </span>

      {isBusy && (
        <span className="flex items-center gap-1.5 text-xs text-foreground/60">
          <span className="h-1.5 w-1.5 rounded-full bg-forecast animate-pulse motion-reduce:hidden" />
          {progressMessages[runState]}
        </span>
      )}
    </div>
  );
}
