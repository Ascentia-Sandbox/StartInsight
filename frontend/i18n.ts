/**
 * i18n Configuration for StartInsight
 * English-only configuration
 */

import { notFound } from 'next/navigation';
import { getRequestConfig } from 'next-intl/server';

// English-only
export const locales = ['en'] as const;
export type Locale = typeof locales[number];

export default getRequestConfig(async ({ locale }) => {
  // Validate that the incoming locale parameter is valid
  const validLocale = locale && locales.includes(locale as Locale) ? locale : 'en';

  return {
    locale: validLocale,
    messages: (await import(`./messages/${validLocale}.json`)).default
  };
});
