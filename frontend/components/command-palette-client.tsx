'use client';
import dynamic from 'next/dynamic';

const CommandPaletteInner = dynamic(
  () => import('@/components/command-palette').then((m) => m.CommandPalette),
  { ssr: false }
);

export function CommandPaletteClient() {
  return <CommandPaletteInner />;
}
