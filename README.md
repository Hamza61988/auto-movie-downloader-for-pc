# Auto Movie Downloader for PC

An automated headless desktop application for PC that uses browser instrumentation and network sniffing to detect webapp player controls, intercept hidden streaming manifests, and download videos directly.

---

## Technical Architecture & Detection Systems

### 1. Gateway & Splash Screen Detection
Web applications often display interstitial verification splash pages before revealing media. The script executes frame-wide DOM queries to detect and trigger gateway elements:
- Detects splash buttons matching `button#b`, `button[id="b"]`, and text pattern `"Continue to Moviesjoy"`.
- Executes force-click dispatching with JavaScript fallback evaluation (`el.click()`) if native event bubbles are intercepted.

### 2. Nested Iframe & Embedded Player Control Detection
Video streaming platforms embed third-party video players (e.g. JWPlayer, VideoJS, custom HTML5 players) inside cross-origin iframes. Standard locators often fail with strict mode conflicts when multiple iframes exist. The engine:
- Traverses all active execution contexts across `page.frames`.
- Detects play triggers matching `button[type="submit"][aria-label="Play"]`.
- Identifies SVG path vectors matching standard play iconography (`d="M8 5v14l11-7z"`).
- Fallback detection for legacy player classes: `#playBtn`, `#bigPlay`, `.jw-bigplay`, `.jw-center`.

### 3. CDP Network Packet Sniffing & Header Extraction
Video manifests are served dynamically via encrypted API handshakes rather than plain HTML tags. The system hooks directly into Chromium network layer via Chrome DevTools Protocol:
- Intercepts outbound requests across both page and worker contexts.
- Detects `.m3u8` HLS manifest files loaded by the internal MSE (Media Source Extensions) buffer.
- Extracts dynamic HTTP headers, specifically cryptographic `Referer` and `Origin` values required by streaming servers to prevent 403 Forbidden errors.

### 4. Manifest V3 Ad-Shielding & Tab Interception
- Boots Chromium with a dedicated persistent profile and loads an unpacked uBlock Origin Lite extension.
- Employs Declarative Net Request rulesets to suppress malicious scripts, click-jacking layers, and tracking beacons.
- Subscribes to browser context `page` events to detect popup windows and terminate unauthorized ad tabs immediately.

### 5. URL Slug & Metadata Parsing
- Normalizes incoming URL paths and strips routing prefixes (`movie-`, `tv-`, `watch-`).
- Detects and strips server hash IDs (5+ alphanumeric characters, e.g. `-2qrgrcx2`) while preserving natural sequel numbering (e.g. `The Dark Knight 2`).
- Sanitizes file paths to generate standardized filenames for local storage.

---

## Setup Instructions

Install the Python libraries and download Chromium for Playwright:

```bash
pip install -r requirements.txt
playwright install chromium
```

Note: uBlock Origin Lite is downloaded and configured automatically into `ublock_lite/` on first execution.

---

## Usage

Run the downloader by providing a movie or episode link:

```bash
python auto_downloader.py <MOVIE_URL>
```

### Example:

```bash
python auto_downloader.py https://moviesjoy.sx/watch/movie-resident-evil-2qrgrcx2
```

Execution Pipeline:
1. Detects title: `Resident Evil`.
2. Initialises Chromium with persistent profile and MV3 ad-blocking enabled.
3. Detects and bypasses splash screen prompts.
4. Locates and triggers playback inside the active player iframe.
5. Sniffs authentic m3u8 playlist URL and captures authorization headers.
6. Transfers payload to yt-dlp and compiles `Resident.Evil.mkv`.

---

## Custom Output Filename

You can specify a custom output filename as a second argument:

```bash
python auto_downloader.py https://moviesjoy.sx/watch/movie-resident-evil-2qrgrcx2 "Resident_Evil_2002.mkv"
```

---

## Supported Platforms

- Windows 10 / 11 (PC)
- Linux / macOS with Python 3.9+
