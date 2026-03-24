'use client';

import Link from "next/link";
import { useState } from "react";
import { Lightbulb, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { config } from "@/lib/env";
import { analytics, Events } from "@/lib/analytics";

const footerLinks = {
  "Browse Ideas": [
    { title: "Idea of the Day", href: "/idea-of-the-day" },
    { title: "Idea Database", href: "/insights" },
    { title: "Trends", href: "/trends" },
    { title: "Market Insights", href: "/market-insights" },
    { title: "Founder Fits", href: "/founder-fits" },
  ],
  Tools: [
    { title: "Idea Generator", href: "/dashboard" },
    { title: "Research Agent", href: "/research" },
    { title: "Builder Integration", href: "/dashboard?tab=builder" },
    { title: "Chat & Strategize", href: "/workspace" },
    { title: "Market Size Calculator", href: "/tools#market-calculator" },
  ],
  Resources: [
    { title: "Platform Tour", href: "/platform-tour" },
    { title: "Features", href: "/features" },
    { title: "Tools Library", href: "/tools" },
    { title: "Pricing", href: "/pricing" },
    { title: "FAQ", href: "/faq" },
  ],
  Company: [
    { title: "About", href: "/about" },
    { title: "Success Stories", href: "/success-stories" },
    { title: "Announcements", href: "/market-insights?category=Announcements" },
    { title: "Contact", href: "/contact" },
  ],
};

export function Footer() {
  const [email, setEmail] = useState('');
  const [nlState, setNlState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [nlMessage, setNlMessage] = useState('');

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setNlState('loading');
    try {
      const res = await fetch(`${config.apiUrl}/api/newsletter/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, source: 'footer' }),
      });
      const data = await res.json();
      if (res.ok) {
        setNlState('success');
        setNlMessage(data.message);
        analytics.track(Events.NEWSLETTER_SIGNUP, { source: 'footer' });
      } else {
        setNlState('error');
        setNlMessage(data.detail || 'Something went wrong.');
      }
    } catch {
      setNlState('error');
      setNlMessage('Network error. Please try again.');
    }
  };

  return (
    <footer className="border-t bg-muted/30 dark:bg-muted/10">
      <div className="container mx-auto px-4 py-12">
        {/* Newsletter Signup */}
        <div className="mb-10 pb-8 border-b text-center max-w-lg mx-auto">
          <h3 className="text-lg font-semibold mb-2">Stay ahead of the market</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Weekly insights on the most promising startup opportunities, backed by data.
          </p>
          {nlState === 'success' ? (
            <div className="flex items-center justify-center gap-2 text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-sm">{nlMessage}</span>
            </div>
          ) : (
            <form onSubmit={handleSubscribe} className="flex gap-2">
              <Input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="flex-1"
                disabled={nlState === 'loading'}
              />
              <Button type="submit" disabled={nlState === 'loading'} size="sm">
                {nlState === 'loading' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Subscribe'
                )}
              </Button>
            </form>
          )}
          {nlState === 'error' && (
            <p className="text-xs text-red-500 mt-2">{nlMessage}</p>
          )}
        </div>

        {/* Link Columns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="font-semibold text-sm mb-3">{category}</h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {link.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="mt-10 pt-6 border-t flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">StartInsight</span>
          </div>
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} StartInsight. All rights reserved.
          </p>
          <div className="flex gap-4">
            <Link
              href="/privacy"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Privacy Policy
            </Link>
            <Link
              href="/terms"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
