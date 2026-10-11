# HYPERSTREAM PHANTOM

Autonomous headless stream interception and media extraction engine for Moviesjoy (`https://moviesjoy.sx`).

HYPERSTREAM PHANTOM deploys Chromium under automated CDP orchestration, injects Manifest V3 ad-shielding (uBlock Origin Lite), bypasses intermediate gatekeeper splash pages, isolates embedded player iframes, captures hidden HLS `.m3u8` transport streams, extracts clean metadata titles, and drives high-speed parallel downloads via `yt-dlp`.

---

## Architecture & Features

- Automated MV3 Shielding: Bootstraps and attaches uBlock Origin Lite dynamically to eliminate popups and redirect traps.
- Frame Traversal Engine: Recursively queries top-level DOM and nested player iframes without strict mode collision.
- Adaptive Click Routing: Detects gatekeeper splash buttons (`button#b`) and interactive player controls (`button[type="submit"][aria-label="Play"]`).
- Passive Traffic Sniffer: Non-invasive packet inspection across main page and worker scopes to catch authentic m3u8 manifests with active session origin and referer tokens.
- Automatic Title Extraction: Normalizes slug structures and strips noise hashes to yield sanitized output filenames.

---

## 1. Quick Setup

Prepare the runtime environment by installing Python dependencies and downloading Chromium:

```bash
pip install -r requirements.txt
playwright install chromium
```

Note: uBlock Origin Lite is retrieved and provisioned automatically on initial execution.

---

## 2. Execution

Run the engine by supplying the target Moviesjoy URL:

```bash
python auto_downloader.py <TARGET_URL>
```

### Example:

```bash
python auto_downloader.py https://moviesjoy.sx/watch/movie-resident-evil-2qrgrcx2
```

Console execution flow:
1. Detects title: `Resident Evil`.
2. Initialises Chromium persistent profile with MV3 ad-blocking active.
3. Bypasses "Continue to Moviesjoy" splash prompt.
4. Auto-triggers playback inside the active embed provider.
5. Sniffs authentic m3u8 playlist URL and headers.
6. Downloads and packages full media to `Resident.Evil.mkv`.

---

## 3. Custom Output Naming

Optionally pass a custom filename as the second argument:

```bash
python auto_downloader.py https://moviesjoy.sx/watch/movie-resident-evil-2qrgrcx2 "Resident_Evil_2002.mkv"
```

---

## Target Domain Support

- Moviesjoy (`https://moviesjoy.sx`, `https://moviesjoy.is`, `https://moviesjoy.to`)
