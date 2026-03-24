'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { config } from '@/lib/env';
import { analytics, Events } from '@/lib/analytics';

interface NewsletterFormProps {
  source?: string;
}

export function NewsletterForm({ source = 'homepage' }: NewsletterFormProps) {
  const [email, setEmail] = useState('');
  const [state, setState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setState('loading');
    try {
      const res = await fetch(`${config.apiUrl}/api/newsletter/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, source }),
      });
      const data = await res.json();
      if (res.ok) {
        setState('success');
        setMessage(data.message);
        analytics.track(Events.NEWSLETTER_SIGNUP, { source });
      } else {
        setState('error');
        setMessage(data.detail || 'Something went wrong.');
      }
    } catch {
      setState('error');
      setMessage('Network error. Please try again.');
    }
  };

  if (state === 'success') {
    return (
      <div className="flex items-center justify-center gap-2 text-green-600">
        <CheckCircle2 className="h-5 w-5" />
        <span>{message}</span>
      </div>
    );
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-2 max-w-md mx-auto">
        <Input
          type="email"
          placeholder="your@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="flex-1"
          disabled={state === 'loading'}
        />
        <Button type="submit" disabled={state === 'loading'}>
          {state === 'loading' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            'Subscribe'
          )}
        </Button>
      </form>
      {state === 'error' && (
        <p className="text-sm text-red-500 mt-2 text-center">{message}</p>
      )}
      <p className="text-xs text-muted-foreground mt-3 text-center">
        By subscribing you agree to our{' '}
        <Link href="/privacy" className="underline underline-offset-2 hover:text-foreground transition-colors">
          Privacy Policy
        </Link>
        . Unsubscribe anytime.
      </p>
    </div>
  );
}
