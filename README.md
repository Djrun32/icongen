# Intranet Icon Generator

Internal web app for generating presentation icons with OpenAI or Gemini image models.

## What this starter includes

- Password-protected login for all users.
- Role-based access control:
  - `admin` users can configure locked generation settings and style presets.
  - normal users can only select an approved style and type a metaphor.
- Admin panel pages:
  - `/admin/styles`: create/enable/disable/delete style presets.
  - `/admin/settings`: update locked prompt/settings and manage users.
- User page:
  - `/generate`: choose style from dropdown + enter metaphor, then generate PNG.
- SQLite storage for users, style presets, and generated icon history.

## Quick start (Ubuntu VM)

1. Install Python 3.10+ and `pip`.
2. Create virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create `.env` from `.env.example` and set:
   - `SECRET_KEY` to a long random value.
   - `OPENAI_API_KEY` (for OpenAI provider) or `GEMINI_API_KEY` (for Gemini provider).
   - `IMAGE_PROVIDER` to `openai` or `gemini`.
   - `IMAGE_MODEL` to your model ID (for example `gpt-image-1` or `gemini-3.1-flash-image-preview`).
   - `INITIAL_ADMIN_PASSWORD` to a secure password.
4. Run the app (`.env` is auto-loaded):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. Open `http://<vm-ip>:8000`.
6. Sign in with `INITIAL_ADMIN_USERNAME` and `INITIAL_ADMIN_PASSWORD`.
7. In `/admin/settings`, you can:
   - update locked generation prompt/limits,
   - choose image provider/model and set or clear a DB-stored provider API key,
   - reset any user password.

## Docker option

```bash
cp .env.example .env
# edit .env
docker compose up -d --build
```

`docker-compose.yml` stores SQLite data in `./data/icongen.db` and generated PNGs in `./app/static/generated`.

## Security notes

- All pages are behind login.
- Admin pages return HTTP 403 for non-admin users.
- Change the default admin password immediately.
- For production intranet use, run behind Nginx/Traefik with HTTPS and set secure cookies.

## Suggested next upgrades

- Add audit logs for admin changes.
- Add API tokens for service-to-service calls.
- Add background jobs for batch icon generation.
- Add Alembic migrations for schema lifecycle management.
