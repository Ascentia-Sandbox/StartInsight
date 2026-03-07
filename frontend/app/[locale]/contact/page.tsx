import { Suspense } from "react";
import { ContactContent } from "./contact-content";

export default function ContactPage() {
  return (
    <Suspense>
      <ContactContent />
    </Suspense>
  );
}
