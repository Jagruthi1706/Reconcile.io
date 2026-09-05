'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api-client';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    try {
      await login(email, password);
      router.replace('/');
    } catch {
      setError('Sign-in failed. Check your credentials.');
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-panel border border-border bg-card p-6 shadow-card">
        <p className="label-accent">Reconcile.io</p>
        <h1 className="mt-2 font-editorial text-3xl">Sign in</h1>
        <div className="mt-6 space-y-4">
          <label className="block text-sm">Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-1 h-10 w-full rounded-control border border-border bg-background px-3" /></label>
          <label className="block text-sm">Password<input required type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-1 h-10 w-full rounded-control border border-border bg-background px-3" /></label>
        </div>
        {error && <p role="alert" className="mt-4 text-sm text-error">{error}</p>}
        <button type="submit" className="mt-6 h-10 w-full rounded-control bg-ink text-sm text-parchment">Sign in</button>
      </form>
    </main>
  );
}