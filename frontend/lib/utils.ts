import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { formatDistanceToNow } from "date-fns"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const MYT_TIMEZONE = "Asia/Kuala_Lumpur";

/** "08 Feb 2026, 4:13 PM MYT" */
export function formatDateTimeMYT(date: string | Date | null): string {
  if (!date) return "-";
  return new Intl.DateTimeFormat("en-MY", {
    timeZone: MYT_TIMEZONE,
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(new Date(date)) + " MYT";
}

/** "08 Feb 2026" */
export function formatDateMYT(date: string | Date | null): string {
  if (!date) return "-";
  return new Intl.DateTimeFormat("en-MY", {
    timeZone: MYT_TIMEZONE,
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(date));
}

/** "2 hours ago" */
export function formatRelativeTime(date: string | Date | null): string {
  if (!date) return "-";
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}
