import subprocess
import asyncio
import os
import sys
import re
import urllib.request
from urllib.parse import urlparse
import zipfile
from playwright.async_api import async_playwright

def extract_movie_name(url):
    path = urlparse(url).path.strip('/')
    slug = path.split('/')[-1] if path else ''
    
    # Strip leading prefixes (movie-, tv-, series-, watch-)
    slug = re.sub(r'^(movie|tv|series|watch)-', '', slug, flags=re.IGNORECASE)
    
    # Strip random hash/ID at the end (5+ alphanumeric chars) while preserving sequel numbers like -2
    slug = re.sub(r'-[a-z0-9]{5,12}$', '', slug, flags=re.IGNORECASE)
    
    words = [w for w in re.split(r'[-_]+', slug) if w]
    return ' '.join(w.capitalize() for w in words)


def ensure_ublock_extension():
    """
    Ensures the uBlock Origin Lite (Manifest V3) extension is downloaded and ready for Chromium.
    Modern Chromium versions require MV3 extensions to run reliably under CDP/Playwright.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ext_dir = os.path.join(base_dir, "ublock_lite")
    manifest_path = os.path.join(ext_dir, "manifest.json")
    
    if not os.path.exists(manifest_path):
        print("[*] Setting up uBlock Origin Lite extension for Chrome...")
        os.makedirs(ext_dir, exist_ok=True)
        zip_path = os.path.join(base_dir, "ublock_lite.zip")
        url = "https://github.com/uBlockOrigin/uBOL-home/releases/download/2026.1006.1931/uBOLite_2026.1006.1931.chromium.zip"
        try:
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(ext_dir)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            print("[*] uBlock Origin Lite installed successfully!")
        except Exception as e:
            print(f"[-] Failed to download uBlock extension: {e}")
            return None
            
    return ext_dir

async def check_and_click_continue(page):
    """
    Detects and clicks the splash/landing button:
    <button id="b">Continue to Moviesjoy</button>
    across the main page and any embedded frames.
    """
    continue_selectors = [
        'button#b',
        'button[id="b"]',
        'button:has-text("Continue to Moviesjoy")',
        'a#b',
        'a:has-text("Continue to Moviesjoy")',
        '#b'
    ]
    
    contexts = [page] + list(page.frames)
    for ctx in contexts:
        for sel in continue_selectors:
            try:
                loc = ctx.locator(sel)
                count = await loc.count()
                for i in range(count):
                    btn = loc.nth(i)
                    if await btn.is_visible():
                        print(f"    [*] Found 'Continue to Moviesjoy' splash button ({sel})! Clicking it...")
                        try:
                            await btn.click(force=True, timeout=3000)
                        except Exception:
                            await btn.evaluate("el => el.click()")
                        await asyncio.sleep(3) # Wait for page transition
                        return True
            except Exception:
                continue
    return False

async def check_and_click_play(page):
    """
    Detects and clicks video play buttons, specifically:
    <button type="submit" aria-label="Play"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"></path></svg></button>
    as well as site player overlays across the main page and all frames/iframes.
    """
    play_selectors = [
        'button[type="submit"][aria-label="Play"]',
        'button[aria-label="Play"]',
        'button:has(svg path[d*="M8 5v14l11-7z"])',
        'button:has(path[d*="M8 5v14l11-7z"])',
        'button:has(svg[aria-hidden="true"])',
        'button#playBtn',
        '#playBtn',
        'button#bigPlay',
        '#bigPlay',
        '.jw-bigplay',
        '.jw-center',
        'div.jw-center',
        'button.play'
    ]
    
    contexts = [page] + list(page.frames)
    for ctx in contexts:
        for sel in play_selectors:
            try:
                loc = ctx.locator(sel)
                count = await loc.count()
                for i in range(count):
                    btn = loc.nth(i)
                    if await btn.is_visible():
                        target_info = getattr(ctx, 'name', '') or getattr(ctx, 'url', 'main page')
                        print(f"    [+] Found Play button ({sel}) in [{target_info}]! Clicking it...")
                        try:
                            await btn.scroll_into_view_if_needed(timeout=1000)
                        except Exception:
                            pass
                        try:
                            await btn.click(force=True, timeout=2000)
                        except Exception:
                            await btn.evaluate("el => el.click()")
                        return True
            except Exception:
                continue
    return False

async def find_m3u8_url(page_url):
    found_m3u8_url = None
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ext_dir = ensure_ublock_extension()
    user_data_dir = os.path.join(base_dir, "chrome_profile")
    
    launch_args = [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled"
    ]
    if ext_dir and os.path.exists(ext_dir):
        # Pass extension arguments to Chromium
        launch_args.extend([
            f"--disable-extensions-except={ext_dir}",
            f"--load-extension={ext_dir}"
        ])
    
    async with async_playwright() as p:
        # Use launch_persistent_context to load Chrome extensions (regular launch does not support extensions)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=launch_args
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        await page.bring_to_front()
        
        # --- AD BLOCKER / POPUP KILLER ---
        # Streaming sites open spam popups when clicked. This immediately kills any new popups!
        async def handle_new_page(new_page):
            if new_page == page:
                return
            # Don't close internal extension pages / background workers
            if new_page.url.startswith("chrome-extension://"):
                return
            try:
                await new_page.close()
                print("    [!] Blocked a popup ad.")
            except Exception:
                pass
        context.on("page", handle_new_page)
        
        # --- NETWORK LISTENER ---
        async def handle_request(request):
            nonlocal found_m3u8_url
            url = request.url
            # Catch ANY m3u8 playlist file requested by the video player
            if '.m3u8' in url:
                if not found_m3u8_url:
                    print(f"\n[+] Intercepted Stream URL: {url.split('?')[0]}...")
                    found_m3u8_url = {
                        "url": url,
                        "referer": request.headers.get("referer", ""),
                        "origin": request.headers.get("origin", "")
                    }
                    
        # Intercept across both page and context for all iframes/workers
        page.on("request", handle_request)
        context.on("request", handle_request)
        
        print(f"[*] Navigating to: {page_url}")
        try:
            await page.goto(page_url, wait_until="domcontentloaded", timeout=45000)
        except Exception:
            pass # Ignore navigation timeouts
            
        await asyncio.sleep(3) # Wait for initial DOM and player elements to render
        
        # --- AUTO-CLICKER ---
        print("[*] Initiating Auto-Clicker to bypass ads and start video...")
        
        # Step 1: Check for "Continue to Moviesjoy" splash screen right after loading
        if await check_and_click_continue(page):
            print("    [*] Successfully clicked 'Continue to Moviesjoy' splash button!")
            await asyncio.sleep(2)
            
        # Step 2: Attempt auto-click loop
        for i in range(12):
            if found_m3u8_url:
                break
            
            try:
                # Re-check splash button in case of redirect
                await check_and_click_continue(page)
                
                # Check and click video play button across all frames
                clicked = await check_and_click_play(page)
                
                if not clicked:
                    # Fallback click in the center of the viewport
                    width = page.viewport_size['width'] if page.viewport_size else 1280
                    height = page.viewport_size['height'] if page.viewport_size else 720
                    await page.mouse.click(width / 2, height / 2)
                    print(f"    [*] Play button not visible, clicked center of screen ({width/2}, {height/2})")
                
                # Save screenshot for debugging on early iterations
                if i in (1, 3):
                    await page.screenshot(path="screenshot.png")
                    print("    [*] Captured screenshot and saved as screenshot.png")
            except Exception as e:
                print(f"    [!] Click loop error: {e}")
                
            # Wait up to 10 seconds for the video buffer and m3u8 request
            for _ in range(10):
                if found_m3u8_url:
                    break
                await asyncio.sleep(1)
            
        await context.close()
        
    return found_m3u8_url

def download_video(stream_data, output_filename):
    print(f"\n[*] Starting yt-dlp download...")
    ytdlp_command = [
        "yt-dlp",
        stream_data["url"],
        "-o", output_filename
    ]
    if stream_data.get("referer"):
        ytdlp_command.extend(["--add-header", f"Referer:{stream_data['referer']}"])
    if stream_data.get("origin"):
        ytdlp_command.extend(["--add-header", f"Origin:{stream_data['origin']}"])
    
    # Retry up to 5 times if Windows locks a file fragment (WinError 32)
    for attempt in range(5):
        print(f"[*] Download attempt {attempt + 1}/5...")
        result = subprocess.run(ytdlp_command)
        if result.returncode == 0:
            print("[*] Download completed successfully!")
            break
        else:
            print(f"[-] Download failed with error code {result.returncode}. Retrying in 5 seconds...")
            import time
            time.sleep(5)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python auto_downloader.py <URL> [output_filename]")
        return
        
    page_url = sys.argv[1]
    movie_name = extract_movie_name(page_url) or "Movie"
    print(f"[*] Detected Title: {movie_name}")
    
    if len(sys.argv) > 2:
        output_filename = sys.argv[2]
        if not output_filename.endswith('.mkv') and not output_filename.endswith('.mp4'):
            output_filename += ".mkv"
    else:
        # Generate clean filename, e.g. "Resident.Evil.mkv"
        safe_name = movie_name.replace(" ", ".")
        output_filename = f"{safe_name}.mkv"
    
    print("========================================")
    print("      Fully Automated Downloader        ")
    print("========================================")
    stream_url = await find_m3u8_url(page_url)
    
    if stream_url:
        print(f"[*] Successfully extracted the hidden stream link!")
        download_video(stream_url, output_filename)
        print(f"\n[*] DONE! Saved as: {output_filename}")
    else:
        print("\n[-] Error: Could not automatically find the stream URL.")

if __name__ == "__main__":
    asyncio.run(main())
