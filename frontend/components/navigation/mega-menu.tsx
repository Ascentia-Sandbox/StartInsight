"use client";

import * as React from "react";
import Link from "next/link";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import { cn } from "@/lib/utils";
import {
  Lightbulb,
  Database,
  TrendingUp,
  BookOpen,
  Sparkles,
  Search,
  Hammer,
  MessageSquare,
  UserCheck,
  Map,
  Layers,
  Wrench,
  DollarSign,
  HelpCircle,
  Building2,
  Trophy,
  Megaphone,
  Mail,
} from "lucide-react";

const browseIdeasItems = [
  {
    title: "Idea of the Day",
    href: "/idea-of-the-day",
    description: "Daily featured startup opportunities hand-picked by our AI.",
    icon: Lightbulb,
  },
  {
    title: "Founder Fits",
    href: "/founder-fits",
    description: "Ideas scored for solo founders and low barrier to entry.",
    icon: UserCheck,
  },
  {
    title: "Idea Database",
    href: "/insights",
    description: "Browse 1000+ validated startup ideas with scoring.",
    icon: Database,
  },
  {
    title: "Trends",
    href: "/trends",
    description: "180+ trending keywords with volume and growth metrics.",
    icon: TrendingUp,
  },
  {
    title: "Market Insights",
    href: "/market-insights",
    description: "Expert analysis and reports on emerging markets.",
    icon: BookOpen,
  },
];

const toolsItems = [
  {
    title: "Idea Generator",
    href: "/dashboard",
    description: "AI-powered startup idea generation from market signals.",
    icon: Sparkles,
  },
  {
    title: "Research Agent",
    href: "/research",
    description: "40-step AI research for deep competitive analysis.",
    icon: Search,
  },
  {
    title: "Builder Integration",
    href: "/dashboard?tab=builder",
    description: "One-click export to Lovable, Bolt, Replit, and more.",
    icon: Hammer,
  },
  {
    title: "Chat & Strategize",
    href: "/workspace",
    description: "Interactive AI chat for strategy refinement.",
    icon: MessageSquare,
  },
  {
    title: "Market Size Calculator",
    href: "/tools#market-calculator",
    description: "Estimate TAM, SAM, SOM for your startup idea.",
    icon: TrendingUp,
  },
];

const resourcesItems = [
  {
    title: "Platform Tour",
    href: "/platform-tour",
    description: "See StartInsight in action with video walkthroughs.",
    icon: Map,
  },
  {
    title: "Features",
    href: "/features",
    description: "Explore 20+ features that set us apart.",
    icon: Layers,
  },
  {
    title: "Tools Library",
    href: "/tools",
    description: "54 essential tools to build your startup.",
    icon: Wrench,
  },
  {
    title: "Pricing",
    href: "/pricing",
    description: "Simple, transparent pricing for every stage.",
    icon: DollarSign,
  },
  {
    title: "FAQ",
    href: "/faq",
    description: "Answers to common questions.",
    icon: HelpCircle,
  },
];

const companyItems = [
  {
    title: "About",
    href: "/about",
    description: "Our mission to democratize startup discovery.",
    icon: Building2,
  },
  {
    title: "Success Stories",
    href: "/success-stories",
    description: "Founders who built successful businesses with us.",
    icon: Trophy,
  },
  {
    title: "Announcements",
    href: "/market-insights?category=Announcements",
    description: "Latest product updates and news.",
    icon: Megaphone,
  },
  {
    title: "Contact",
    href: "/contact",
    description: "Get in touch with our team.",
    icon: Mail,
  },
];

interface ListItemProps extends React.ComponentPropsWithoutRef<"a"> {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  href: string;
}

const ListItem = React.forwardRef<React.ElementRef<"a">, ListItemProps>(
  ({ className, title, children, icon: Icon, href, ...props }, ref) => {
    return (
      <li>
        <NavigationMenuLink asChild>
          <Link
            ref={ref}
            href={href}
            className={cn(
              "block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
              className
            )}
            {...props}
          >
            <div className="flex items-center gap-2">
              {Icon && <Icon className="h-4 w-4 text-primary" />}
              <div className="text-sm font-medium leading-none">{title}</div>
            </div>
            <p className="line-clamp-2 text-sm leading-snug text-muted-foreground mt-1">
              {children}
            </p>
          </Link>
        </NavigationMenuLink>
      </li>
    );
  }
);
ListItem.displayName = "ListItem";

export function MegaMenu() {
  return (
    <NavigationMenu className="hidden md:flex">
      <NavigationMenuList>
        {/* Browse Ideas */}
        <NavigationMenuItem data-tour="browse-ideas">
          <NavigationMenuTrigger>Browse Ideas</NavigationMenuTrigger>
          <NavigationMenuContent>
            <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
              {browseIdeasItems.map((item) => (
                <ListItem
                  key={item.title}
                  title={item.title}
                  href={item.href}
                  icon={item.icon}
                >
                  {item.description}
                </ListItem>
              ))}
            </ul>
          </NavigationMenuContent>
        </NavigationMenuItem>

        {/* Tools */}
        <NavigationMenuItem data-tour="tools">
          <NavigationMenuTrigger>Tools</NavigationMenuTrigger>
          <NavigationMenuContent>
            <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
              {toolsItems.map((item) => (
                <ListItem
                  key={item.title}
                  title={item.title}
                  href={item.href}
                  icon={item.icon}
                >
                  {item.description}
                </ListItem>
              ))}
            </ul>
          </NavigationMenuContent>
        </NavigationMenuItem>

        {/* Resources */}
        <NavigationMenuItem data-tour="resources">
          <NavigationMenuTrigger>Resources</NavigationMenuTrigger>
          <NavigationMenuContent>
            <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
              {resourcesItems.map((item) => (
                <ListItem
                  key={item.title}
                  title={item.title}
                  href={item.href}
                  icon={item.icon}
                >
                  {item.description}
                </ListItem>
              ))}
            </ul>
          </NavigationMenuContent>
        </NavigationMenuItem>

        {/* Company */}
        <NavigationMenuItem>
          <NavigationMenuTrigger>Company</NavigationMenuTrigger>
          <NavigationMenuContent>
            <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2">
              {companyItems.map((item) => (
                <ListItem
                  key={item.title}
                  title={item.title}
                  href={item.href}
                  icon={item.icon}
                >
                  {item.description}
                </ListItem>
              ))}
            </ul>
          </NavigationMenuContent>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenu>
  );
}

// Export menu items for mobile menu
export { browseIdeasItems, toolsItems, resourcesItems, companyItems };
