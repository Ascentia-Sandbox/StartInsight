"use client";

import * as React from "react";
import Link from "next/link";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  browseIdeasItems,
  toolsItems,
  resourcesItems,
  companyItems,
} from "./mega-menu";

interface MobileMenuProps {
  isAuthenticated: boolean;
  onSignIn?: () => void;
}

export function MobileMenu({ isAuthenticated, onSignIn }: MobileMenuProps) {
  const [open, setOpen] = React.useState(false);

  const closeMenu = () => setOpen(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Open menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[300px] sm:w-[400px]">
        <SheetHeader>
          <SheetTitle>
            <Link href="/" onClick={closeMenu} className="text-xl font-bold">
              StartInsight
            </Link>
          </SheetTitle>
        </SheetHeader>
        <div className="mt-6 flex flex-col gap-4">
          <Accordion type="single" collapsible className="w-full">
            {/* Browse Ideas */}
            <AccordionItem value="browse-ideas">
              <AccordionTrigger className="text-base font-medium">
                Browse Ideas
              </AccordionTrigger>
              <AccordionContent>
                <div className="flex flex-col gap-2 pl-4">
                  {browseIdeasItems.map((item) => (
                    <Link
                      key={item.title}
                      href={item.href}
                      onClick={closeMenu}
                      className="flex items-center gap-2 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <item.icon className="h-4 w-4 text-primary" />
                      {item.title}
                    </Link>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Tools */}
            <AccordionItem value="tools">
              <AccordionTrigger className="text-base font-medium">
                Tools
              </AccordionTrigger>
              <AccordionContent>
                <div className="flex flex-col gap-2 pl-4">
                  {toolsItems.map((item) => (
                    <Link
                      key={item.title}
                      href={item.href}
                      onClick={closeMenu}
                      className="flex items-center gap-2 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <item.icon className="h-4 w-4 text-primary" />
                      {item.title}
                    </Link>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Resources */}
            <AccordionItem value="resources">
              <AccordionTrigger className="text-base font-medium">
                Resources
              </AccordionTrigger>
              <AccordionContent>
                <div className="flex flex-col gap-2 pl-4">
                  {resourcesItems.map((item) => (
                    <Link
                      key={item.title}
                      href={item.href}
                      onClick={closeMenu}
                      className="flex items-center gap-2 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <item.icon className="h-4 w-4 text-primary" />
                      {item.title}
                    </Link>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Company */}
            <AccordionItem value="company">
              <AccordionTrigger className="text-base font-medium">
                Company
              </AccordionTrigger>
              <AccordionContent>
                <div className="flex flex-col gap-2 pl-4">
                  {companyItems.map((item) => (
                    <Link
                      key={item.title}
                      href={item.href}
                      onClick={closeMenu}
                      className="flex items-center gap-2 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <item.icon className="h-4 w-4 text-primary" />
                      {item.title}
                    </Link>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          {/* Auth Section */}
          <div className="mt-4 pt-4 border-t">
            {isAuthenticated ? (
              <div className="flex flex-col gap-2">
                <Link
                  href="/dashboard"
                  onClick={closeMenu}
                  className="block py-2 text-sm font-medium hover:text-primary transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  href="/workspace"
                  onClick={closeMenu}
                  className="block py-2 text-sm font-medium hover:text-primary transition-colors"
                >
                  My Workspace
                </Link>
                <Link
                  href="/settings"
                  onClick={closeMenu}
                  className="block py-2 text-sm font-medium hover:text-primary transition-colors"
                >
                  Settings
                </Link>
              </div>
            ) : (
              <Button asChild className="w-full">
                <Link href="/auth/login" onClick={closeMenu}>
                  Sign in
                </Link>
              </Button>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
