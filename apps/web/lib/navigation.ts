import { LayoutDashboard, GitCompareArrows, AlertTriangle, ReceiptText, TrendingUp, MessageSquareText, CreditCard, Target, ScrollText, Settings, type LucideIcon } from 'lucide-react';

export interface NavRoute {
  label: string;
  href: string;
  icon: LucideIcon;
  description: string;
}

export const navRoutes: NavRoute[] = [
  { label: 'Overview', href: '/', icon: LayoutDashboard, description: 'What happened?' },
  { label: 'Reconcile', href: '/reconcile', icon: GitCompareArrows, description: 'What matched and what didn’t?' },
  { label: 'Exceptions', href: '/exceptions', icon: AlertTriangle, description: 'What needs my attention?' },
  { label: 'Tax', href: '/tax', icon: ReceiptText, description: 'What requires tax review?' },
  { label: 'Forecast', href: '/forecast', icon: TrendingUp, description: 'What does this mean for future cash?' },
  { label: 'Copilot', href: '/copilot', icon: MessageSquareText, description: 'Why did this happen?' },
  { label: 'Razorpay', href: '/razorpay', icon: CreditCard, description: 'Live test-mode integration' },
  { label: 'Accuracy', href: '/accuracy', icon: Target, description: 'Can I trust the engine?' },
  { label: 'Audit', href: '/audit', icon: ScrollText, description: 'Can I prove what happened?' },
  { label: 'Settings', href: '/settings', icon: Settings, description: 'How is the system configured?' },
];
