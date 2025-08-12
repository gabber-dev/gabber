# Gabber Frontend

The Gabber frontend is the web UI for building and running apps. It talks to the `editor`, `engine`, and `repository` services.

## Quickstart

Option A — start everything from the repo root:

```bash
make all
```

Option B — run only the frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000

## Notes

- The frontend expects the backend services to be running. Use `make all` from the repo root to start them.
- See the top‑level README for details: ../README.md
