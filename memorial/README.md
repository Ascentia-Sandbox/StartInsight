# startinsight.co — Memorial

A single-page editorial post-mortem hosted at <https://startinsight.co>.

In lieu of the product that used to live here.

## Files

- `frontend/index.html` — the entire site (45KB, embedded CSS + minimal JS, Google Fonts: Fraunces, Newsreader, JetBrains Mono)
- `frontend/robots.txt`, `frontend/sitemap.xml`
- `vercel.json` — static deploy config (framework: null, no build)

## Redeploy

```
vercel --prod --yes
```

The directory is linked to `ascentias-projects/start-insight` (existing Vercel project). The `startinsight.co` domain auto-aliases to the latest production deployment.

## Edit

Edit `frontend/index.html` directly. It's intentionally one file — easier to grep, harder to drift, never breaks on framework upgrades. Re-run the redeploy command above.

## Source content

The post-mortem text lives in two places:

1. `memory-bank/post-mortem.md` in the original [StartInsight repo](https://github.com/Ascentia-Sandbox/StartInsight) — the canonical long-form version.
2. `frontend/index.html` here — the public editorial version.

Keep them in sync.
