import Link from "next/link";
import { Lightbulb } from "lucide-react";

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
  return (
    <footer className="border-t bg-muted/30 dark:bg-muted/10">
      <div className="container mx-auto px-4 py-12">
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
