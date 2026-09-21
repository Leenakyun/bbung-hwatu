# Railway deployment

Project layout:

- `frontend/` - browser UI
- `backend/` - Flask API, auth, game engine, SSE realtime

## Railway settings

Root Directory:
`/`

Start Command:
`gunicorn --chdir backend --bind 0.0.0.0:$PORT --workers 1 --threads 100 --timeout 0 app:app`

Healthcheck Path:
`/api/health`

Replica:
`1`

## Volume

Attach a Railway Volume with mount path:

`/data`

The app automatically uses Railway's `RAILWAY_VOLUME_MOUNT_PATH`.

Persistent files:
- `/data/users.db`
- `/data/logs/game_events.log`

## Optional environment variables

- `BBUNG_ROOM_TTL_HOURS=6`
- `BBUNG_ROOM_CLEANUP_INTERVAL_SECONDS=600`

Do not set Railway Root Directory to `/backend`, because the Flask app serves the sibling `frontend/` directory.
