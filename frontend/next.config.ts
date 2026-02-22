// StartInsight Frontend Configuration
import type { NextConfig } from "next";
import createNextIntlPlugin from 'next-intl/plugin';
import { withSentryConfig } from "@sentry/nextjs";

const withNextIntl = createNextIntlPlugin('./i18n.ts');

const nextConfig: NextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_SENTRY_RELEASE: process.env.VERCEL_GIT_COMMIT_SHA ?? 'local',
  },
};

// Wrap with both next-intl and Sentry
export default withSentryConfig(
  withNextIntl(nextConfig),
  {
    // For all available options, see:
    // https://github.com/getsentry/sentry-webpack-plugin#options

    org: process.env.SENTRY_ORG || "startinsight",
    project: process.env.SENTRY_PROJECT || "frontend",

    // Only print logs for uploading source maps in CI
    silent: !process.env.CI,

    // For all available options, see:
    // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

    // Upload a larger set of source maps for prettier stack traces (increases build time)
    widenClientFileUpload: true,

    // Source maps configuration
    sourcemaps: {
      // Hide source maps from generated client bundles
      deleteSourcemapsAfterUpload: true,
    },

    // Automatically tree-shake Sentry logger statements to reduce bundle size
    bundleSizeOptimizations: {
      excludeDebugStatements: true,
    },
  }
);
