'use client';

import { useEffect } from 'react';
import * as Sentry from '@sentry/nextjs';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error('Global application error:', error);
  }, [error]);

  return (
    <html>
      <body>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '2rem',
          fontFamily: 'system-ui, sans-serif'
        }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '1rem', color: '#ef4444' }}>
            Critical Error
          </h1>
          <p style={{ marginBottom: '1rem', color: '#6b7280' }}>
            A critical error occurred. Please try refreshing the page.
          </p>
          {error.message && (
            <div style={{
              padding: '1rem',
              backgroundColor: '#f3f4f6',
              borderRadius: '0.5rem',
              marginBottom: '1rem',
              maxWidth: '600px',
              width: '100%'
            }}>
              <p style={{ fontSize: '0.875rem', fontFamily: 'monospace' }}>{error.message}</p>
              {error.digest && (
                <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>
                  Error ID: {error.digest}
                </p>
              )}
            </div>
          )}
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              onClick={reset}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                fontSize: '1rem'
              }}
            >
              Try again
            </button>
            <a
              href="/"
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: 'white',
                color: '#3b82f6',
                border: '1px solid #3b82f6',
                borderRadius: '0.375rem',
                textDecoration: 'none',
                fontSize: '1rem'
              }}
            >
              Go to Homepage
            </a>
          </div>
        </div>
      </body>
    </html>
  );
}
