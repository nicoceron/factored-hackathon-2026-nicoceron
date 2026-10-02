# Free sandbox deployment

The service uses Render's Free web-service plan: one Docker instance, 0.1 CPU and 512 MB RAM. The existing Hobby workspace had no payment card when configured. No paid add-on, persistent disk, external model subscription or paid inference is required. `render.yaml` records the reproducible service settings; the dashboard service is created from the reviewed public GitHub repository.

## Release procedure

1. Run `make check`, `node --check src/factored_banking/static/app.js`, `git diff --check`, and the configured secret scanner. Confirm no organizer records, source PDFs or credentials are tracked.
2. Build the source-only image with `make docker`; smoke-test the actual HTTP service with `python3 scripts/smoke.py http://127.0.0.1:8097`.
3. Open a pull request, wait for GitHub CI on its current head, and merge the reviewed commit.
4. Deploy that merged commit manually. Auto-deploy stays off so unverified pushes cannot replace the demonstrated release.
5. Verify `/healthz`, `/readyz`, all static assets, secure cookie attributes, and the complete ES/PT customer-to-analyst workflow on the public HTTPS origin. Save only aggregate receipts.
6. A rollback deploys the previous reviewed commit from Render's manual-deploy menu. Re-run readiness and the HTTP smoke check.

## Service configuration

- Runtime: Docker; repository-root `Dockerfile`; Oregon region.
- Plan: **Free ($0/month)**, single instance and worker.
- Health check: `/readyz` (checks storage and released language model).
- `CLARO_SECURE=1`; `CLARO_ORIGIN` is the exact public HTTPS origin.
- `CLARO_DB=/state/claro.sqlite` is set in the image; the app runs as UID 10001.
- The image uses Render's `PORT` variable and disables Uvicorn access logs.
- No credentials or organizer records are uploaded. Public demo data and policies are explicitly team-authored fixtures.

## Free-host limits

Render documents that free web services sleep after 15 minutes without inbound traffic and can take about a minute to wake. Reviewers should open the demo before recording or judging. There is no uptime/SLA claim and no artificial keepalive job.

Free-service filesystem state is ephemeral: cases, sessions and analytics may disappear on restart, redeploy or idle spin-down. The app verifies committed state during the running instance, but the host does not provide durable banking storage. The UI and submission instructions identify this limitation. A local Docker volume provides durable developer testing; actual banking operation requires managed durable storage and real identity.

Free instance hours, bandwidth and build minutes have provider limits. The service uses the free allowance and no payment card was added. If allowances are exhausted, accept suspension rather than upgrade or buy capacity. This prototype is not a production banking deployment.

## Verification receipt

Public URL, deployed commit, check timestamp and measured outcomes are recorded in [SUBMISSION.md](SUBMISSION.md) and the final aggregate release receipt after public verification. A configured dashboard form or successful local Docker build alone is not deployment proof.

## References

- [Render free-service behavior and limits](https://render.com/docs/free)
- [Render Docker deployment](https://render.com/docs/docker)
- [Render manual deployment and rollback controls](https://render.com/docs/deploys)
