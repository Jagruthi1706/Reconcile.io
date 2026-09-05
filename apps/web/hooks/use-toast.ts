import { useState } from 'react';

interface ToastOptions {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

export function useToast() {
  const [toast, setToast] = useState<ToastOptions | null>(null);

  return {
    toast: (options: ToastOptions) => setToast(options),
    toastState: toast,
  };
}
