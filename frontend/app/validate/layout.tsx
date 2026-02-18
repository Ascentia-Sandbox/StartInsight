'use client';

import { Providers } from '../providers';
import { ThemeProvider } from 'next-themes';

export default function ValidateLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <Providers>
        {children}
      </Providers>
    </ThemeProvider>
  );
}
