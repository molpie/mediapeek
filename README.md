# MediaPeek

A minimal self-hosted web UI for inspecting media file metadata via `ffprobe`.

**No database. No scanning. No indexing.** Just browse your mounted volumes and click a file.

## Stack

- **Backend**: FastAPI + Python 3.12 (Alpine)
- **Frontend**: Single-page HTML/JS — no Node, no build step
- **Engine**: `ffprobe` (from `ffmpeg` Alpine package)

## Quick start

```bash
# Edit docker-compose.yml — set your media path(s)
docker compose up -d
# Open http://localhost:8080
```

## Manual build

```bash
docker build -t mediapeek .
docker run -d \
  --name mediapeek \
  -p 8080:8080 \
  -v /your/media:/media:ro \
  mediapeek
```

## Multiple media roots

Mount multiple directories under `/media`:

```yaml
volumes:
  - /mnt/nas/movies:/media/movies:ro
  - /mnt/nas/series:/media/series:ro
  - /mnt/nas/music:/media/music:ro
```

## Behind nginx (recommended)

```nginx
location /mediapeek/ {
    proxy_pass http://127.0.0.1:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## What it shows

**Format / Container**: format name, duration, file size, overall bitrate  
**Tags**: embedded metadata (title, artist, date, comment, etc.)  
**Video streams**: codec, profile, resolution, aspect ratio, pixel format, frame rate, bitrate, bit depth, color space/range/primaries/transfer, chroma location, field order  
**Audio streams**: codec, profile, sample rate, channels, channel layout, sample format, bit depth, bitrate, language, default/forced flags  
**Subtitle streams**: codec, language, title, disposition flags  

## Security

- Path traversal protection: all paths are resolved and checked against `MEDIA_ROOT`
- All volumes mounted `:ro` (read-only) — ffprobe never writes
- No auth built-in — put it behind oauth2-proxy or restrict to LAN/VPN
