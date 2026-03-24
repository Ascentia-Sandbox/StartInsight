'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { config } from '@/lib/env';

export default function NewsletterConfirmPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('Invalid confirmation link.');
      return;
    }

    fetch(`${config.apiUrl}/api/newsletter/confirm/${token}`)
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setStatus('success');
          setMessage(data.message || 'Your subscription is confirmed!');
        } else {
          setStatus('error');
          setMessage(data.detail || 'Confirmation failed.');
        }
      })
      .catch(() => {
        setStatus('error');
        setMessage('Something went wrong. Please try again.');
      });
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Card className="max-w-md w-full">
        <CardContent className="pt-8 pb-6 text-center space-y-4">
          {status === 'loading' && (
            <>
              <Loader2 className="h-10 w-10 mx-auto animate-spin text-primary" />
              <p className="text-muted-foreground">Confirming your subscription...</p>
            </>
          )}
          {status === 'success' && (
            <>
              <CheckCircle2 className="h-10 w-10 mx-auto text-green-500" />
              <h2 className="text-xl font-semibold">{message}</h2>
              <p className="text-muted-foreground">
                You&apos;ll receive weekly insights on the most promising startup opportunities.
              </p>
              <Button asChild>
                <Link href="/">Browse Insights</Link>
              </Button>
            </>
          )}
          {status === 'error' && (
            <>
              <XCircle className="h-10 w-10 mx-auto text-red-500" />
              <h2 className="text-xl font-semibold">Confirmation Failed</h2>
              <p className="text-muted-foreground">{message}</p>
              <Button asChild variant="outline">
                <Link href="/">Back to Home</Link>
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
