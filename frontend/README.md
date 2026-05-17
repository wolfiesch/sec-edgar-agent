# SEC EDGAR Frontend

React + TypeScript + Vite client for the SEC EDGAR Agent API.

## API Authentication

The browser bundle must not contain `API_KEY` or any `VITE_*` API-key value.
Vite exposes `VITE_*` variables to every user who downloads the JavaScript.

Local development works through the Vite dev proxy, which injects `DEV_API_KEY`
server-side when forwarding `/api` requests. Production deployments need a
trusted server-side proxy or session-backed backend that adds `X-API-Key`
outside the browser.

The current static Vercel rewrite to the Fly backend cannot add this secret
safely. Treat protected production chat as blocked until that server-side auth
layer exists.

```bash
DEV_API_KEY=sec-api-demo npm run dev
```

`sec-api-demo` is local-only. Do not set a production backend to accept it.

## Development

```bash
npm install
npm run dev
```

```bash
npm run build
```
