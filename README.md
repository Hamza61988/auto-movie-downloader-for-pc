# Moviesjoy Movie Scraper

An automated website movie scraper and stream downloader for Moviesjoy (`https://moviesjoy.sx`).

This scraper launches Chromium with uBlock Origin Lite (Manifest V3) enabled, bypasses gatekeeper splash pages, isolates the video player within embedded iframes, extracts the hidden HLS m3u8 playlist URL, parses the clean movie title from the link, and downloads the full media file using yt-dlp.

---

## Features

- Built-in Ad Shielding: Automatically installs and loads uBlock Origin Lite to block popups, redirect loops, and malicious overlays.
- Iframe Player Navigation: Recursively inspects all iframe frames on the page to find and click the Play button without locator conflicts.
- Intermediate Page Bypass: Automatically clicks "Continue to Moviesjoy" splash screens (`button#b`).
- Hidden Stream Interception: Captures authentic `.m3u8` playlist requests alongside session headers (Referer and Origin).
- Automatic Title Sanitization: Extracts clean, human-readable titles (e.g. `Resident Evil`) and sets formatted output filenames (`Resident.Evil.mkv`).

---

## 1. Setup Instructions

Install dependencies and download Chromium for Playwright:

```bash
pip install -r requirements.txt
playwright install chromium
```

Note: The script automatically handles downloading the uBlock Origin Lite extension on first run.

---

## 2. Usage

Run the scraper by passing any Moviesjoy movie or TV episode URL:

```bash
python auto_downloader.py <MOVIE_URL>
```

### Example:

```bash
python auto_downloader.py https://moviesjoy.sx/watch/movie-resident-evil-2qrgrcx2
```

What the scraper does automatically:
1. Detects title: `Resident Evil`.
2. Launches browser with ad-blocking active.
3. Clicks "Continue to Moviesjoy" if the splash page appears.
4. Triggers the embedded video player Play button.
5. Sniffs the m3u8 streaming link.
6. Downloads the full movie and saves it as `Resident.Evil.mkv`.

---

## 3. Optional: Custom Output Filename

You can specify a custom output filename as a second argument:

```bash
python auto_downloader.py https://moviesjoy.sx/watch/movie-resident-evil-2qrgrcx2 "Resident_Evil_2002.mkv"
```

---

## Target Site

- Moviesjoy (`https://moviesjoy.sx`, `https://moviesjoy.is`, `https://moviesjoy.to`)
