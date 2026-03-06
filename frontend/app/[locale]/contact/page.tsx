import { Suspense } from "react";
import { ContactContent } from "./contact-content";

export const dynamic = 'force-static';

export default function ContactPage() {
  return (
    <Suspense>
      <ContactContent />
    </Suspense>
  );
}
