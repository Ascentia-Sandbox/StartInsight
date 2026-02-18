'use client';

/**
 * Language Switcher Component
 * Phase 15.5: APAC Multi-language Support
 *
 * Dropdown for switching between 6 supported languages
 * Fixed: Works without next-intl client context (uses pathname detection)
 */

import { usePathname, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Globe } from 'lucide-react';
import { useState, useMemo } from 'react';

type Language = {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
};

const LANGUAGES: Language[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'zh-CN', name: 'Chinese (Simplified)', nativeName: '简体中文', flag: '🇨🇳' },
  { code: 'id-ID', name: 'Indonesian', nativeName: 'Bahasa Indonesia', flag: '🇮🇩' },
  { code: 'vi-VN', name: 'Vietnamese', nativeName: 'Tiếng Việt', flag: '🇻🇳' },
  { code: 'th-TH', name: 'Thai', nativeName: 'ภาษาไทย', flag: '🇹🇭' },
  { code: 'tl-PH', name: 'Tagalog', nativeName: 'Tagalog', flag: '🇵🇭' },
  { code: 'ja-JP', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
  { code: 'ko-KR', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
];

const SUPPORTED_LOCALES = ['zh-CN', 'id-ID', 'vi-VN', 'th-TH', 'tl-PH', 'ja-JP', 'ko-KR'];

export function LanguageSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  // Detect current locale from pathname
  const currentLocale = useMemo(() => {
    // Check if pathname starts with English locale first
    if (pathname.startsWith('/en/') || pathname === '/en') {
      return 'en';
    }
    // Then check other supported locales
    for (const locale of SUPPORTED_LOCALES) {
      if (pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`) {
        return locale;
      }
    }
    return 'en'; // Default to English
  }, [pathname]);

  const currentLanguage = LANGUAGES.find(lang => lang.code === currentLocale) || LANGUAGES[0];

  const handleLanguageChange = (languageCode: string) => {
    // Remove current locale from pathname
    let pathnameWithoutLocale = pathname;

    // Check all locales including English
    const allLocales = ['en', ...SUPPORTED_LOCALES];
    for (const locale of allLocales) {
      if (pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`) {
        // Remove locale prefix: /en/page -> /page or /en -> /
        pathnameWithoutLocale = pathname.substring(locale.length + 1) || '/';
        break;
      }
    }

    // Add new locale prefix (all locales including English get a prefix with 'always' mode)
    const newPathname = `/${languageCode}${pathnameWithoutLocale === '/' ? '' : pathnameWithoutLocale}`;

    setIsOpen(false);
    router.push(newPathname);
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        className="relative"
        aria-label="Change language"
      >
        <Globe className="h-5 w-5" />
      </Button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-64 rounded-md shadow-lg bg-background border z-50">
            <div className="p-2">
              <div className="px-3 py-2 text-xs font-medium text-muted-foreground">
                Select Language
              </div>
              {LANGUAGES.map((language) => (
                <button
                  key={language.code}
                  onClick={() => handleLanguageChange(language.code)}
                  className={`
                    w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md
                    hover:bg-muted transition-colors
                    ${language.code === currentLocale ? 'bg-muted font-medium' : ''}
                  `}
                >
                  <span className="text-xl">{language.flag}</span>
                  <div className="flex-1 text-left">
                    <div className="font-medium">{language.nativeName}</div>
                    <div className="text-xs text-muted-foreground">{language.name}</div>
                  </div>
                  {language.code === currentLocale && (
                    <svg 
                      className="h-4 w-4 text-primary" 
                      fill="none" 
                      viewBox="0 0 24 24" 
                      stroke="currentColor"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M5 13l4 4L19 7" 
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
