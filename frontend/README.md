# ClipDock frontend

Spanish export workspace built with Next.js App Router, TypeScript and Tailwind CSS. All media operations go **directly from the browser to the independent backend**. There is no Vercel API proxy, frontend media worker, sample product metadata, persisted capability token or platform embed.

## Run locally

Node.js 20.9 or newer is required by Next.js (verified against its official installation documentation). This workspace was exercised with Node 26.5.1. Dependencies are reproducible with `package-lock.json`.

```sh
cd /opt/data/projects/clipdock/frontend
npm ci
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 npm run dev -- --port 3000
```

Start the actual FastAPI backend separately on port 8000 and allow the frontend origin in its CORS settings. Alternatively copy `.env.example` to `.env.local` and set the actual backend origin. A configured origin does not mean a backend is running.

Check the independent service directly:

```sh
curl -f http://127.0.0.1:8000/health
```

## Production

Set `NEXT_PUBLIC_API_URL` to the **real deployed HTTPS backend origin** before building. The value is mandatory for a usable workspace: an omitted or invalid value displays an honest configuration-unavailable screen instead of pointing to an invented endpoint. Absolute origin only, with no credentials, path, query or fragment. HTTP is permitted only for localhost/loopback development.

```sh
NEXT_PUBLIC_API_URL=https://YOUR-ACTUAL-BACKEND-HOST npm run build
npm run start
```

The example hostname is a placeholder, not a deployed backend. `NEXT_PUBLIC_*` values are frozen during Next.js build; rebuild after changing the backend. Vercel project root must be `frontend`. No deployment was performed by this frontend task.

## Verify

```sh
npm test
npm run typecheck
npm run build
npm audit
```

Vitest and React Testing Library UI tests were developed in vertical RED → GREEN cycles. Network responses in tests are explicit test fixtures, not real-platform integration evidence. Tests cover rights gating, backend inspect/jobs payloads, MP4/MP3, Original quality `0`, unavailable audio/video, stale replies, URL and permission invalidation, polling progress/failure/deadline, request timeout, unmount cleanup, external-download rejection, thumbnail failure, expired inspection, empty/loading state and missing server configuration. Security tests cover hostname spoofing, absolute API origins, HTTPS thumbnail CDN allowlist and same-origin API download paths.

## Runtime boundaries

- Authorization is a user's affirmation, not an automated ownership verification. Both inspect and jobs requests send `authorized: true` only after affirmative permission; revocation clears inspection and cancels frontend work.
- Inspection and each API request time out after 45 seconds. Job polling occurs every two seconds and stops after ten minutes. Retry is manual, never an infinite retry loop.
- Aborting the frontend prevents stale UI updates; it does not claim to delete or cancel a job already accepted by the backend.
- Backend thumbnail policy is mirrored exactly: `i.ytimg.com`, `img.youtube.com`, `i9.ytimg.com`, `pbs.twimg.com`, `video.twimg.com`, HTTPS only. Unsupported or failed thumbnails use an accessible fallback. No autoplay or video player is fabricated; the API exposes only thumbnails.
- Downloads require the configured API origin and `/api/` pathname. Capability secrets remain only in component memory and the temporary direct download URL; no local/session storage or cookies.
- CSP `connect-src` is scoped to the configured origin. CDN image sources are exact, not wildcard. Third-party scripts, frames and objects are blocked. Next.js static bootstrap requires inline scripts; `unsafe-eval` is permitted only in development. Security headers include no-referrer, nosniff, DENY framing and disabled camera/microphone/location/payment.
- Platform compatibility is conditional. Private media, DRM, cookies and restriction evasion are explicitly excluded.

## Design

Light export desk: cool-gray canvas, white sheet, fine seams, navy controls, system typography and Lucide icons. URL/permission/thumbnail sit left of the export settings on desktop; the workspace stacks on mobile. Reduced motion and keyboard focus states are supported. Root PRODUCT.md and SURFACE.md own the approved direction.
