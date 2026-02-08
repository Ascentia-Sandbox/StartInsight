import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.ENVIRONMENT || "development",

  // Tracing
  tracesSampleRate: 0.1, // 10% of transactions for performance monitoring

  // Note: Session Replay is only available on the client side
});
